from dataclasses import replace

import pytest

from apps.adviser_v2.demo.bakeoff import Score, complete_cell, freeze, paired_models_match, winner
from apps.adviser_v2.demo.evidence import (
    MAP_SETTINGS,
    PROCESSING_VERSION,
    build_sections,
    cache_matches,
    map_ranges,
    pack_sections,
)


def pages():
    rows, offset = [], 0
    for p in range(1, 5):
        text = f"Original page {p}. A policy condition ends here."
        rows.append({"physical_page": p, "passage": text, "evidence_span_id": f"p{p}",
                     "document_char_start": offset})
        offset += len(text) + 1
    return rows


def tree():
    return {"tree": {"doc_description": "NAV_DESCRIPTION_SECRET", "structure": [
        {"node_id": "a", "title": "Policy", "summary": "NAV_SUMMARY_SECRET", "start_index": 2,
         "end_index": 4, "nodes": [{"node_id": "b", "title": "Benefit", "summary": "NAV_CHILD_SECRET",
                                     "start_index": 3, "end_index": 3}]}]}}


def sections(saved=None):
    return build_sections(plan_id="p", document={"sha256": "x", "document_version_id": "d"},
                          pages=pages(), saved_map=saved or tree())


def test_summary_isolation_and_full_source_coverage():
    pieces, nav, reason = sections()
    assert reason is None
    assert "NAV_SUMMARY_SECRET" in str(nav) and "NAV_DESCRIPTION_SECRET" in str(nav)
    assert "NAV_" not in str(pack_sections("p", pieces).evidence())
    assert "NAV_" not in " ".join(s.index_text for s in pieces)
    assert [(s.page, s.text) for c in pieces for s in c.segments] == [(p["physical_page"], p["passage"]) for p in pages()]
    assert len(pieces) == 4  # front matter, parent prefix, child, parent suffix


def test_bad_map_gets_recorded_fallback():
    saved = tree()
    saved["tree"]["structure"][0]["nodes"][0]["end_index"] = 5
    pieces, nav, reason = sections(saved)
    assert "parent" in reason and all(c.fallback for c in pieces)
    assert all(n["fallback"] for n in nav)
    assert "NAV_" not in str(nav)


def test_crossing_siblings_rejected_and_shared_boundary_kept_once():
    nodes = [{"node_id": "a", "title": "A", "summary": "a", "start_index": 1, "end_index": 3},
             {"node_id": "b", "title": "B", "summary": "b", "start_index": 2, "end_index": 4}]
    with pytest.raises(ValueError, match="cross"):
        map_ranges(nodes, 4)
    nodes[1]["start_index"] = 3
    result = map_ranges(nodes, 4)
    assert sum(b - a + 1 for a, b, _, _ in result) == 4


def test_cache_requires_model_settings_and_source_identity():
    saved = {"pdf_sha256": "pdf", "raw_sha256": "raw", "sdk_revision": "sdk",
             "processing_version": PROCESSING_VERSION, "settings": MAP_SETTINGS, "models": ["claude-sonnet-5"]}
    assert cache_matches(saved, pdf_sha="pdf", raw_sha="raw", sdk_revision="sdk")
    for field, value in [("models", ["gpt-5.6-sol"]), ("settings", {}), ("raw_sha256", "changed")]:
        assert not cache_matches({**saved, field: value}, pdf_sha="pdf", raw_sha="raw", sdk_revision="sdk")


def test_packet_omissions_and_plan_scope():
    pieces, _, _ = sections()
    packet = pack_sections("p", pieces, budget=1)
    assert not packet.sections and len(packet.omitted_ids) == len(pieces)
    with pytest.raises(ValueError, match="Wrong-plan"):
        pack_sections("p", [replace(pieces[0], plan_id="foreign")])


def test_both_queries_are_required_for_complete_star_cell():
    assert not complete_cell({"a", "b"}, {"a", "b"}, {"a"})
    assert complete_cell({"a", "b"}, {"a", "b"}, {"a", "b", "c"})


def test_protocol_v2_rejected_quotes_do_not_disqualify():
    h, p = Score("H", 39, 260, 0, 99), Score("P", 39, 250, 0, 0)
    assert winner(h, p)["winner"] == "P"
    assert not h.disqualified
    assert winner(Score("H", 39, 260, 1, 0), Score("P", 0, 0, 0, 0))["winner"] == "P"
    outcome = winner(Score("H", 39, 260, 1, 0), Score("P", 39, 259, 1, 0))
    assert outcome["winner"] == "H" and outcome["both_disqualified"] and outcome["live_enabled"]


def test_fixed_denominators_and_frozen_resume(tmp_path):
    assert Score("H", 0, 130, 0, 0, 130).score == 19.5
    with pytest.raises(ValueError):
        Score("P", 39, 261, 0, 0)
    assert freeze(tmp_path, {"questions": "one"}) == freeze(tmp_path, {"questions": "one"})
    with pytest.raises(ValueError, match="changed"):
        freeze(tmp_path, {"questions": "tuned"})


def test_split_model_pair_is_invalid():
    assert paired_models_match({"models": ["claude-sonnet-5"]}, {"models": ["claude-sonnet-5"]})
    assert not paired_models_match({"models": ["gpt-5.6-luna"]}, {"models": ["claude-sonnet-5"]})
    assert not paired_models_match({"models": []}, {"models": []})


def test_failed_map_resume_uses_recorded_fallback_without_repeating_ai(tmp_path, monkeypatch):
    from apps.adviser_v2.demo.mapping import build_corpus
    called = []
    monkeypatch.setattr('apps.adviser_v2.demo.mapping.configure_sdk', lambda: (None, None))
    def failure(*args):
        called.append(1)
        raise RuntimeError('Invalid ordered map')
    monkeypatch.setattr('apps.adviser_v2.demo.mapping.build_document', failure)
    original = pages()
    for p in original:
        p['document_version_id'] = 'd'
    corpus = {'plans': [{'policy_version_id': 'p', 'pages': original,
                        'documents': [{'document_version_id': 'd', 'sha256': 'source'}]}]}
    first = build_corpus(corpus, tmp_path)
    second = build_corpus(corpus, tmp_path)
    assert len(called) == 1
    assert first['plans'][0]['sections'] == second['plans'][0]['sections']
    assert first['plans'][0]['document_status'][0]['status'] == 'fallback'


def test_pageindex_transport_retry_is_not_a_negative_title_check(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from apps.adviser_v2.demo.mapping import CONTEXT, internal_call
    from apps.adviser_v2.demo.relay import RelayUnavailable
    calls = []
    def call(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RelayUnavailable('temporary transport failure')
        return SimpleNamespace(value={'response': '{"answer":"yes"}'}, model='gpt-5.6-luna', call_ids=['call'])
    relay = SimpleNamespace(state=SimpleNamespace(model=lambda: 'gpt-5.6-luna'), call=call)
    errors = []
    token = CONTEXT.set((relay, tmp_path, set(), errors))
    monkeypatch.setattr('apps.adviser_v2.demo.mapping.time.sleep', lambda _: None)
    try:
        result = internal_call('ignored', 'Directly return the final JSON structure.')
    finally:
        CONTEXT.reset(token)
    assert result == '{"answer":"yes"}' and len(calls) == 2 and not errors


def test_packet_budget_counts_serialized_metadata_and_tables():
    import json

    from apps.adviser_v2.evidence_retrieval import token_count
    pieces, _, _ = sections()
    cells = {str(n): {'row': n, 'column': 1, 'citation': {
        'section_id': pieces[0].id, 'page_id': 'p1', 'quote': 'Original page 1.'}}
        for n in range(100)}
    packet = pack_sections('p', pieces, budget=750, tables=[{'id': 'large', 'cells': cells}])
    assert packet.sections
    assert 'table:large' in packet.omitted_ids
    assert token_count(json.dumps(packet.evidence(), ensure_ascii=False)) <= 750
    assert 'NAV_' not in str(packet.evidence())
