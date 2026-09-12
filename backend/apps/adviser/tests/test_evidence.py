import gzip
import hashlib
import json

import pytest
from django.test import override_settings

from apps.adviser.evidence import create_evidence_bundle, validate_evidence_span
from apps.adviser.models import (
    DocumentPage,
    DocumentVersion,
    ExtractionRevision,
    SourceBlob,
)
from apps.adviser.source_maps import DocumentValidationError, _page_map, store_pdf_bytes


class TwoColumnPage:
    width = 600
    height = 800
    rotation = 0
    cropbox = (0, 0, 600, 800)
    mediabox = (0, 0, 600, 800)

    def extract_words(self, **_options):
        words = []
        for top, left_number, right_number in ((100, "one", "one"), (120, "two", "two")):
            words.extend(
                [
                    {"text": "Left", "x0": 40, "x1": 80, "top": top, "bottom": top + 10},
                    {
                        "text": left_number,
                        "x0": 85,
                        "x1": 120,
                        "top": top,
                        "bottom": top + 10,
                    },
                    {
                        "text": "Right",
                        "x0": 340,
                        "x1": 390,
                        "top": top,
                        "bottom": top + 10,
                    },
                    {
                        "text": right_number,
                        "x0": 395,
                        "x1": 430,
                        "top": top,
                        "bottom": top + 10,
                    },
                ]
            )
        return words


def test_two_column_lines_are_numbered_in_reading_order() -> None:
    page_map = _page_map(TwoColumnPage(), 0)
    assert [line["text"] for line in page_map["lines"]] == [
        "Left one",
        "Left two",
        "Right one",
        "Right two",
    ]
    assert [line["region"] for line in page_map["lines"]] == [
        "left-column",
        "left-column",
        "right-column",
        "right-column",
    ]


@pytest.mark.django_db
def test_existing_content_address_is_verified_before_reuse(tmp_path) -> None:
    content = b"%PDF-1.4\nfixture\n%%EOF\n"
    with override_settings(DATA_ROOT=tmp_path):
        blob = store_pdf_bytes(content)
        (tmp_path / blob.stored_path).write_bytes(b"corrupt")
        with pytest.raises(DocumentValidationError, match="content address"):
            store_pdf_bytes(content)


@pytest.mark.django_db
def test_evidence_resolves_only_frozen_words(tmp_path) -> None:
    artifact = {
        "schema_version": 1,
        "document_id": "",
        "revision": 1,
        "pages": [
            {
                "physical_index": 0,
                "words": [
                    {"id": "p0-w1", "text": "No", "bbox": [10, 10, 20, 20]},
                    {"id": "p0-w2", "text": "copay", "bbox": [22, 10, 50, 20]},
                    {"id": "p0-w3", "text": "applies", "bbox": [10, 25, 40, 35]},
                ],
                "lines": [
                    {
                        "number": 1,
                        "region": "body",
                        "word_ids": ["p0-w1", "p0-w2"],
                        "text": "No copay",
                    },
                    {
                        "number": 2,
                        "region": "body",
                        "word_ids": ["p0-w3"],
                        "text": "applies",
                    },
                ],
            }
        ],
    }
    blob = SourceBlob.objects.create(
        sha256="1" * 64,
        stored_path="source-blobs/11/source.pdf",
        byte_size=10,
        media_type="application/pdf",
    )
    document = DocumentVersion.objects.create(
        blob=blob,
        document_type="policy_wording",
        identity="Fixture",
    )
    artifact["document_id"] = str(document.id)
    compressed = gzip.compress(json.dumps(artifact).encode(), mtime=0)
    relative = "extractions/test/map.json.gz"
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    target.write_bytes(compressed)
    revision = ExtractionRevision.objects.create(
        document_version=document,
        revision=1,
        parser_manifest={},
        artifact_sha256=hashlib.sha256(compressed).hexdigest(),
        source_map_path=relative,
    )
    page = DocumentPage.objects.create(
        extraction_revision=revision,
        physical_index=0,
        width="100",
        height="100",
    )
    with override_settings(DATA_ROOT=tmp_path):
        bundle = create_evidence_bundle(page, 1, 1, "No copay evidence")
        span = bundle.spans.get()
        validate_evidence_span(span)
        assert span.quote == "No copay"
        assert span.source_word_ids == ["p0-w1", "p0-w2"]
        assert span.geometry == [[10, 10, 20, 20], [22, 10, 50, 20]]

        span.quote = "No copay altered"
        span.save(update_fields=["quote"])
        with pytest.raises(DocumentValidationError, match="differs"):
            validate_evidence_span(span)
        span.quote = "No copay"
        span.save(update_fields=["quote"])

        multi_line = create_evidence_bundle(page, 1, 2, "Two-line evidence")
        assert multi_line.spans.get().quote == "No copay\napplies"

        target.write_bytes(b"tampered")
        with pytest.raises(DocumentValidationError, match="hash"):
            create_evidence_bundle(page, 1, 1, "Tampered")
