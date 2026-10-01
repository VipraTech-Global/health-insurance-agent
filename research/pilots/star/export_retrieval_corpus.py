"""Run via the isolated Django shell; export only approved public policy evidence."""

import json
from dataclasses import asdict
from pathlib import Path

from apps.adviser_v2.embedding import qualified_embedding_status
from apps.adviser_v2.evidence_retrieval import index_raw_chunks, raw_chunks
from apps.adviser_v2.models import EvidenceSpan, PolicyVersion, ProcessingJob
from apps.adviser_v2.processing.artifacts import read_artifact
from apps.adviser_v2.processing.manifest_v2 import ANCHOR_PREFIX, raw_bundle_passages
from django.conf import settings

root = Path(settings.BASE_DIR).parent
manifest = json.loads(
    (root / "data/manifests/star-three-plan-2026-09-30-captured.json").read_text()
)
output = Path(settings.COVERGUIDE_REPORT_ROOT) / "retrieval-benchmark"
output.mkdir(parents=True, exist_ok=True)
plans = []
for product in manifest["products"]:
    version = PolicyVersion.objects.get(pk=product["policy_version_id"])
    pages = raw_bundle_passages(version, include_prospectus=True)
    chunks = raw_chunks(str(version.id), pages)
    index_raw_chunks(chunks)
    documents = {}
    for page in pages:
        span = EvidenceSpan.objects.select_related("page__original_file").get(
            pk=page["evidence_span_id"]
        )
        original = span.page.original_file
        documents[page["document_sha256"]] = {
            "sha256": page["document_sha256"],
            "document_key": page["document_key"],
            "document_version_id": page["document_version_id"],
            "path": str(Path(settings.COVERGUIDE_V2_STORAGE_ROOT) / original.storage_key),
        }
    base = next(d for d in product["documents"] if d["role"] == "base_wording")
    job = ProcessingJob.objects.filter(
        source_capture_id=base["capture_id"], stage="validate", state="succeeded"
    ).latest("created_at")
    facts = read_artifact(job)["criteria"]
    assert len(facts) == 13 and all(f["status"] == "supported" for f in facts)
    references = {}
    for fact in facts:
        refs = []
        for citation in fact["citations"]:
            anchor = json.loads(
                next(
                    n.removeprefix(ANCHOR_PREFIX)
                    for n in citation["context"]["notes"]
                    if n.startswith(ANCHOR_PREFIX)
                )
            )
            refs.append(
                {
                    "id": citation["evidence_span_id"],
                    "page_span_id": citation["context"]["span_ids"][0],
                    "start": anchor["start"],
                    "end": anchor["end"],
                    "quote": citation["quote"],
                }
            )
        references[fact["criterion"]] = refs
    plans.append(
        {
            "plan": product["product_key"],
            "policy_version_id": str(version.id),
            "validation_job_id": str(job.id),
            "documents": list(documents.values()),
            "pages": pages,
            "chunks": [asdict(c) for c in chunks],
            "references": references,
        }
    )
ready, reason, _qualification = qualified_embedding_status()
payload = {
    "manifest_sha256": manifest["manifest_sha256"],
    "dense_qualified": ready,
    "dense_reason": reason,
    "tokenizer": "o200k_base",
    "chunk_tokens": 1024,
    "overlap_tokens": 128,
    "plans": plans,
}
(output / "corpus.json").write_text(json.dumps(payload, ensure_ascii=False))
print(
    json.dumps(
        {
            "corpus": str(output / "corpus.json"),
            "plans": len(plans),
            "chunks": sum(len(p["chunks"]) for p in plans),
            "dense_qualified": ready,
            "unique_reference_spans": len(
                {r["id"] for p in plans for refs in p["references"].values() for r in refs}
            ),
        }
    )
)
