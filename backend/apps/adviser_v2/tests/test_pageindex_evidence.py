import hashlib
import json
from dataclasses import replace
from types import SimpleNamespace

import httpx
import pytest
from research_workspace.legacy_v2.evidence_retrieval import pack
from research_workspace.legacy_v2.pageindex_evidence import (
    SDK_REVISION,
    PageIndexFailure,
    original_page_ranking,
    relay_nodes,
    search_prompt,
    selected_nodes,
    tree_nodes,
)
from research_workspace.legacy_v2.source_answers import answer_question


def tree_fixture(tmp_path):
    pages = [
        dict(
            document_version_id="doc",
            document_key="wording",
            document_sha256="a" * 64,
            evidence_span_id=str(number),
            physical_page=number,
            document_char_start=offset,
            passage=text,
        )
        for number, offset, text in [
            (1, 0, "Original first clause.\n"),
            (2, 23, "Original second clause.\n"),
        ]
    ]
    tree = {
        "pdf_sha256": "a" * 64,
        "raw_sha256": hashlib.sha256(
            json.dumps([p["passage"] for p in pages]).encode()
        ).hexdigest(),
        "sdk_revision": SDK_REVISION,
        "tree": {
            "structure": [
                {
                    "node_id": "0001",
                    "title": "Parent",
                    "summary": "GENERATED SUMMARY IS NOT EVIDENCE",
                    "start_index": 1,
                    "end_index": 2,
                    "nodes": [
                        {"node_id": "0002", "title": "Child", "start_index": 2, "end_index": 2}
                    ],
                }
            ]
        },
    }
    path = tmp_path / ("a" * 64 + ".json")
    path.write_text(json.dumps(tree))
    return pages, tree, path


def test_tree_identity_and_original_page_offsets_survive_selection(tmp_path):
    pages, _tree, _path = tree_fixture(tmp_path)
    nodes = tree_nodes(pages, tmp_path)
    ids = selected_nodes('{"nodes":["doc:0002","doc:0001"]}', nodes)
    ranking = original_page_ranking("own-plan", nodes, ids, pages)
    assert [c.id for c in ranking] == ["2", "1"]
    assert [c.text for c in ranking] == [pages[1]["passage"], pages[0]["passage"]]
    assert all("GENERATED" not in c.text for c in ranking)
    assert ranking[0].segments[0]["page"] == 2
    assert ranking[0].segments[0]["document_start"] == 23
    packet = pack("own-plan", ranking, budget=ranking[0].tokens, method="pageindex")
    assert packet.chunks == (ranking[0],) and packet.omitted_chunks == 1
    assert packet.tokens <= packet.budget
    assert search_prompt(nodes, "Is ambulance covered?").endswith(
        "\nQUESTION: Is ambulance covered?"
    )


@pytest.mark.parametrize("mutation", ["pdf_sha256", "raw_sha256", "sdk_revision", "page"])
def test_wrong_tree_hash_revision_and_page_are_rejected(tmp_path, mutation):
    pages, tree, path = tree_fixture(tmp_path)
    if mutation == "page":
        tree["tree"]["structure"][0]["end_index"] = 3
    else:
        tree[mutation] = "wrong"
    path.write_text(json.dumps(tree))
    with pytest.raises(PageIndexFailure):
        tree_nodes(pages, tmp_path)


@pytest.mark.parametrize(
    "output", ['{"nodes":["foreign:0001"]}', '{"nodes":[7]}', '{"nodes":"doc:0001"}', "not JSON"]
)
def test_wrong_plan_or_malformed_selection_never_becomes_evidence(tmp_path, output):
    pages, _tree, _path = tree_fixture(tmp_path)
    with pytest.raises(PageIndexFailure):
        selected_nodes(output, tree_nodes(pages, tmp_path))


def test_unavailable_tree_keeps_a_specific_unknown_without_an_answer_call(monkeypatch):
    packet = replace(
        pack("own-plan", [], budget=16000, method="pageindex"),
        unavailable_reason="The verified tree is missing.",
    )
    monkeypatch.setattr(
        "research_workspace.legacy_v2.source_answers._relay",
        lambda *a, **k: pytest.fail("Unverifiable retrieval reached inference"),
    )
    answer = answer_question(None, "Is AYUSH covered?", {}, packet)
    assert answer.unknown_reason == packet.unavailable_reason
    assert answer.extraction is None


def test_pageindex_transport_retry_keeps_route_checks_and_token_usage(
    monkeypatch, settings, tmp_path
):
    settings.COVERGUIDE_REPORT_ROOT = tmp_path
    settings.COVERGUIDE_POLICY_EXTRACTION_MODEL = "gpt-5.6-sol"
    checked = []
    monkeypatch.setattr(
        "research_workspace.legacy_v2.pageindex_evidence.qualified_route", lambda *a: checked.append(a)
    )
    monkeypatch.setattr(
        "research_workspace.legacy_v2.pageindex_evidence.provider_config",
        lambda *a: SimpleNamespace(base_url="http://127.0.0.1:8317", api_key="synthetic"),
    )
    calls = []

    def post(url, **kwargs):
        calls.append(kwargs)
        if len(calls) < 3:
            raise httpx.ReadTimeout("synthetic timeout")
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "model": "gpt-5.6-sol",
                "status": "completed",
                "usage": {"input_tokens": 10, "output_tokens": 3},
                "output": [
                    {"content": [{"type": "output_text", "text": '{"nodes":["doc:0001"]}'}]}
                ],
            },
        )

    monkeypatch.setattr("research_workspace.legacy_v2.pageindex_evidence.httpx.post", post)
    nodes = [{"id": "doc:0001"}]
    assert relay_nodes("Question", nodes, "own-plan") == ["doc:0001"]
    assert len(checked) == 1 and len(calls) == 3
    assert all(c["json"]["reasoning"]["effort"] == "low" for c in calls)
    log = [
        json.loads(line)
        for line in (tmp_path / "pageindex-live-calls.jsonl").read_text().splitlines()
    ]
    assert [r["status"] for r in log] == ["failed", "failed", "completed"]
    assert log[-1]["usage"]["input_tokens"] == 10
    assert all("wall_ms" in r for r in log)


@pytest.mark.parametrize(
    "response_data",
    [
        [],
        {"model": "unexpected", "status": "completed"},
        {"model": "gpt-5.6-sol", "status": "incomplete"},
        {"model": "gpt-5.6-sol", "status": "completed", "output": [None]},
        {
            "model": "gpt-5.6-sol",
            "status": "completed",
            "output": [{"content": [{"type": "output_text", "text": None}]}],
        },
    ],
)
def test_invalid_relay_output_is_an_explicit_retrieval_failure(
    monkeypatch, settings, tmp_path, response_data
):
    settings.COVERGUIDE_REPORT_ROOT = tmp_path
    settings.COVERGUIDE_POLICY_EXTRACTION_MODEL = "gpt-5.6-sol"
    monkeypatch.setattr("research_workspace.legacy_v2.pageindex_evidence.qualified_route", lambda *a: None)
    monkeypatch.setattr(
        "research_workspace.legacy_v2.pageindex_evidence.provider_config",
        lambda *a: SimpleNamespace(base_url="http://127.0.0.1:8317", api_key="synthetic"),
    )
    monkeypatch.setattr(
        "research_workspace.legacy_v2.pageindex_evidence.httpx.post",
        lambda url, **kwargs: httpx.Response(
            200, request=httpx.Request("POST", url), json=response_data
        ),
    )
    with pytest.raises(PageIndexFailure):
        relay_nodes("Question", [{"id": "doc:0001"}], "own-plan")
    records = (tmp_path / "pageindex-live-calls.jsonl").read_text().splitlines()
    assert len(records) == 1  # Validation failures are not transport retries.
    assert json.loads(records[0])["status"] == "failed"


def test_unqualified_route_cannot_call_pageindex(monkeypatch, settings):
    settings.COVERGUIDE_POLICY_EXTRACTION_MODEL = "gpt-5.6-sol"

    def reject(*args):
        raise ValueError("Unqualified route")

    monkeypatch.setattr("research_workspace.legacy_v2.pageindex_evidence.qualified_route", reject)
    monkeypatch.setattr(
        "research_workspace.legacy_v2.pageindex_evidence.httpx.post",
        lambda *a, **k: pytest.fail("Unqualified route reached the relay"),
    )
    with pytest.raises(ValueError, match="Unqualified"):
        relay_nodes("Question", [{"id": "doc:0001"}], "own-plan")
