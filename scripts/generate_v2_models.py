"""Generate the 61 replacement-app models from the approved r25 field authority.

Account remains ``accounts.User``. This generator intentionally handles only the
mechanical field surface; the reviewed cross-row invariants live in the integrity
migration and domain services, where they can be transactionally enforced.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/design/entity-field-dictionary.json"
OUTPUT = ROOT / "backend/apps/adviser_v2/models"

GROUPS = {
    "customer": {
        "Person",
        "PersonRelationship",
        "Conversation",
        "Message",
        "ConversationMessageChunk",
        "CustomerStatement",
        "CustomerProfileRevision",
        "CustomerFact",
        "CustomerRequirement",
        "AdviceRequest",
        "CustomerPolicy",
        "CustomerPolicyRevision",
        "PolicyMember",
        "CustomerPolicyOption",
        "CustomerPolicyFact",
        "Quote",
        "ConsentRecord",
        "DeletionRequest",
    },
    "corpus": {
        "Insurer",
        "DiscoveryRun",
        "SourceURL",
        "SourceObservation",
        "SourceCapture",
        "OriginalFile",
        "CustomerUploadedDocument",
        "DocumentSeries",
        "DocumentVersion",
        "DocumentPage",
        "EvidenceSpan",
    },
    "catalogue": {
        "Product",
        "PolicyVersion",
        "PolicyVersionDocument",
        "ProductVariant",
        "ProductOption",
        "PolicyRule",
        "PolicyRuleEvidence",
        "PolicyRuleLink",
        "PolicyRuleTableCell",
        "ProviderLocation",
        "ProviderNetworkSnapshot",
        "ProviderNetworkEntry",
        "KnowledgeRelease",
        "KnowledgeReleaseRule",
        "KnowledgeChannel",
        "PolicySearchChunk",
        "PolicyPackageComponent",
    },
    "recommendations": {
        "Recommendation",
        "PolicyCandidateAssessment",
        "PolicyRequirementMatch",
        "InformationNeed",
        "RecommendationStatement",
        "RecommendationCitation",
        "Calculation",
    },
    "operations": {
        "Turn",
        "TurnEvent",
        "Outbox",
        "ModelRoute",
        "ModelQualification",
        "ModelAttempt",
        "ProcessingJob",
        "AuditEvent",
    },
}

ENCRYPTED_FIELDS = {
    ("Person", "display_name"),
    ("Conversation", "title"),
    ("Message", "content"),
    ("CustomerStatement", "resolution_note"),
    ("CustomerUploadedDocument", "display_name"),
    ("EvidenceSpan", "quote"),
    ("Quote", "insurer_quote_reference"),
    ("InformationNeed", "reason"),
    ("RecommendationStatement", "text"),
}

UNIQUE_FIELDS: dict[str, list[tuple[list[str], str | None, bool]]] = {
    "PersonRelationship": [
        (["owner", "from_person", "to_person", "relationship_type", "valid_from", "valid_to"], None, True)
    ],
    "Conversation": [],
    "Message": [
        (["conversation", "sequence"], None, False),
        (["owner", "client_request_id"], "Q(client_request_id__isnull=False)", False),
        (["recommendation"], "Q(recommendation__isnull=False)", False),
    ],
    "ConversationMessageChunk": [(["message", "chunk_index", "index_revision"], None, False)],
    "CustomerProfileRevision": [(["conversation", "revision"], None, False)],
    "DiscoveryRun": [(["session_id"], None, False)],
    "SourceURL": [(["url"], None, False)],
    "OriginalFile": [
        (["owner", "sha256"], None, True),
        (["storage_key"], None, False),
    ],
    "DocumentPage": [(["original_file", "page_number"], None, False)],
    "PolicyVersionDocument": [(["policy_version", "document_version", "role"], None, False)],
    "ProductVariant": [(["policy_version", "name"], None, False)],
    "ProductOption": [(["product_variant", "name"], None, False)],
    "CustomerPolicyRevision": [(["customer_policy", "revision_number"], None, False)],
    "CustomerPolicyOption": [(["customer_policy_revision", "product_option"], None, False)],
    "CustomerPolicyFact": [
        (["supersedes"], "Q(supersedes__isnull=False)", False)
    ],
    "PolicyRule": [
        (["supersedes"], "Q(supersedes__isnull=False)", False),
    ],
    "PolicyRuleEvidence": [(["policy_rule", "evidence_span", "role"], None, False)],
    "PolicyRuleLink": [(["from_policy_rule", "to_policy_rule", "link_type"], None, False)],
    "PolicyRuleTableCell": [(["policy_rule", "selectors"], None, False)],
    "ProviderLocation": [(["supersedes"], "Q(supersedes__isnull=False)", False)],
    "ProviderNetworkEntry": [
        (["provider_network_snapshot", "provider_location", "network_status"], None, False)
    ],
    "KnowledgeRelease": [(["release_number"], None, False)],
    "KnowledgeReleaseRule": [(["knowledge_release", "policy_rule"], None, False)],
    "KnowledgeChannel": [(["name"], None, False)],
    "PolicySearchChunk": [(["document_version", "index_version", "chunk_sha256"], None, False)],
    "Recommendation": [(["turn"], None, False)],
    "PolicyCandidateAssessment": [
        (["recommendation", "product_variant", "selection_commitment"], None, False),
        (
            ["recommendation", "rank"],
            "Q(rank__isnull=False, disposition__in=['recommended', 'alternative'])",
            False,
        ),
    ],
    "PolicyRequirementMatch": [(["candidate_assessment", "customer_requirement"], None, False)],
    "InformationNeed": [
        (["recommendation", "subject_person", "need_kind", "information_key"], None, True)
    ],
    "RecommendationStatement": [(["recommendation", "ordinal"], None, False)],
    "RecommendationCitation": [
        (["recommendation_statement", "evidence_span", "role"], None, False)
    ],
    "Turn": [(["owner", "request_id"], None, False)],
    "TurnEvent": [(["turn", "sequence"], None, False)],
    "Outbox": [(["event_type", "idempotency_key"], None, False)],
    "ModelRoute": [(["route_key"], None, False)],
    "ModelQualification": [
        (["route", "schema_name", "schema_sha256", "created_at"], None, False)
    ],
    "ProcessingJob": [
        (
            ["source_capture", "stage", "input_commitment", "attempt_number"],
            "Q(source_capture__isnull=False)",
            False,
        ),
        (
            ["customer_uploaded_document", "stage", "input_commitment", "attempt_number"],
            "Q(customer_uploaded_document__isnull=False)",
            False,
        ),
    ],
    "PolicyPackageComponent": [(["package_policy_version", "slot_key"], None, False)],
}

CHECKS: dict[str, list[str]] = {
    "PersonRelationship": [
        "~Q(from_person=F('to_person'))",
        "Q(valid_to__isnull=True) | Q(valid_from__isnull=True) | Q(valid_to__gte=F('valid_from'))",
    ],
    "Message": ["Q(sequence__gt=0)"],
    "ConversationMessageChunk": [
        "Q(chunk_index__gte=0)",
        "Q(start_offset__gte=0) & Q(end_offset__gt=F('start_offset'))",
    ],
    "CustomerStatement": ["Q(start_offset__gte=0) & Q(end_offset__gt=F('start_offset'))"],
    "CustomerProfileRevision": ["Q(revision__gt=0)"],
    "CustomerFact": ["Q(schema_version__gt=0)"],
    "DiscoveryRun": [
        "~Q(status__in=['completed', 'failed', 'cancelled']) | Q(completed_at__isnull=False)",
        "~Q(status='failed') | (Q(error_summary__isnull=False) & ~Q(error_summary=''))",
    ],
    "SourceObservation": [
        "~Q(disposition='irrelevant') | (Q(disposition_reason__isnull=False) & ~Q(disposition_reason=''))"
    ],
    "SourceCapture": [
        "Q(http_status__isnull=True) | (Q(http_status__gte=100) & Q(http_status__lte=599))",
        "~Q(status='captured') | (Q(original_file__isnull=False) & Q(completed_at__isnull=False))",
        "~Q(status='failed') | (Q(error_summary__isnull=False) & Q(completed_at__isnull=False))",
        "~Q(status='running') | Q(completed_at__isnull=True)",
    ],
    "OriginalFile": ["Q(byte_size__gte=0)"],
    "DocumentVersion": [
        "Q(effective_to__isnull=True) | Q(effective_from__isnull=True) | Q(effective_to__gte=F('effective_from'))"
    ],
    "DocumentPage": ["Q(page_number__gt=0)"],
    "EvidenceSpan": [
        "(Q(source_capture__isnull=False) & Q(customer_uploaded_document__isnull=True)) | (Q(source_capture__isnull=True) & Q(customer_uploaded_document__isnull=False))"
    ],
    "PolicyRuleLink": ["~Q(from_policy_rule=F('to_policy_rule'))"],
    "ProviderNetworkEntry": [
        "Q(effective_to__isnull=True) | Q(effective_from__isnull=True) | Q(effective_to__gte=F('effective_from'))"
    ],
    "KnowledgeRelease": [
        "Q(release_number__gt=0)",
        "(Q(state='draft') & Q(published_at__isnull=True)) | (Q(state__in=['published', 'retired']) & Q(published_at__isnull=False))",
    ],
    "PolicyCandidateAssessment": ["Q(rank__isnull=True) | Q(rank__gt=0)"],
    "InformationNeed": [
        "~Q(status='asked') | Q(asked_in_message__isnull=False)",
        "~Q(status='resolved') | Q(resolved_in_profile_revision__isnull=False)",
    ],
    "RecommendationStatement": [
        "(Q(candidate_assessment__isnull=True) & Q(requirement_match__isnull=True) & Q(information_need__isnull=True)) | (Q(candidate_assessment__isnull=False) & Q(requirement_match__isnull=True) & Q(information_need__isnull=True)) | (Q(candidate_assessment__isnull=True) & Q(requirement_match__isnull=False) & Q(information_need__isnull=True)) | (Q(candidate_assessment__isnull=True) & Q(requirement_match__isnull=True) & Q(information_need__isnull=False))"
    ],
    "Turn": [
        "~Q(state='running') | (Q(lease_token__isnull=False) & Q(lease_until__isnull=False))",
        "Q(deadline__gt=F('created_at'))",
    ],
    "TurnEvent": ["Q(sequence__gt=0)"],
    "Outbox": [
        "(Q(turn__isnull=False) & Q(processing_job__isnull=True) & Q(knowledge_release__isnull=True)) | (Q(turn__isnull=True) & Q(processing_job__isnull=False) & Q(knowledge_release__isnull=True)) | (Q(turn__isnull=True) & Q(processing_job__isnull=True) & Q(knowledge_release__isnull=False))",
        "~Q(state='leased') | Q(lease_until__isnull=False)",
    ],
    "ModelAttempt": [
        "(Q(turn__isnull=False) & Q(processing_job__isnull=True)) | (Q(turn__isnull=True) & Q(processing_job__isnull=False))",
        "Q(attempt_number__gt=0)",
        "Q(completed_at__isnull=True) | Q(completed_at__gte=F('started_at'))",
        "(Q(response_storage_key__isnull=True) & Q(response_storage_sha256__isnull=True)) | (Q(response_storage_key__isnull=False) & Q(response_storage_sha256__isnull=False))",
    ],
    "ProcessingJob": [
        "(Q(source_capture__isnull=False) & Q(customer_uploaded_document__isnull=True)) | (Q(source_capture__isnull=True) & Q(customer_uploaded_document__isnull=False))",
        "Q(attempt_number__gte=1) & Q(attempt_number__lte=3)",
        "~Q(state='running') | (Q(lease_token__isnull=False) & Q(lease_until__isnull=False))",
        "(Q(result_storage_key__isnull=True) & Q(result_storage_sha256__isnull=True)) | (Q(result_storage_key__isnull=False) & Q(result_storage_sha256__isnull=False))",
    ],
    "ConsentRecord": [
        "(~Q(status='revoked') & Q(revoked_at__isnull=True)) | (Q(status='revoked') & Q(revoked_at__isnull=False))"
    ],
    "DeletionRequest": [
        "~Q(state='completed') | Q(completed_at__isnull=False)",
        "~Q(state='failed') | Q(error_code__isnull=False)",
    ],
    "PolicyPackageComponent": [
        "~Q(review_status='reviewed') | (Q(component_product__isnull=False) & Q(evidence_span__isnull=False))"
    ],
}

INDEXES: dict[str, list[tuple[str, list[str]]]] = {
    "Conversation": [("btree", ["owner", "-updated_at"])],
    "Message": [("btree", ["conversation", "sequence"])],
    "ConversationMessageChunk": [
        ("gin", ["lexical_vector"]),
        ("hnsw", ["embedding"]),
    ],
    "CustomerFact": [("gin", ["value"])],
    "CustomerRequirement": [("gin", ["target_value"])],
    "PolicySearchChunk": [("gin", ["lexical_vector"]), ("hnsw", ["embedding"])],
    "Turn": [("btree", ["state", "lease_until"])],
    "Outbox": [("btree", ["state", "available_at"])],
    "ProcessingJob": [("btree", ["state", "lease_until"])],
}


def snake(value: str) -> str:
    with_word_boundaries = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", with_word_boundaries).lower()


def safe_name(entity: str, suffix: str) -> str:
    base = f"v2_{snake(entity)}_{suffix}"
    if len(base) <= 60:
        return base
    digest = hashlib.sha1(base.encode()).hexdigest()[:8]
    return f"{base[:51]}_{digest}"


def safe_index_name(entity: str, suffix: str) -> str:
    base = f"v2_{snake(entity)}_{suffix}"
    if len(base) <= 30:
        return base
    digest = hashlib.sha1(base.encode()).hexdigest()[:8]
    return f"{base[:21]}_{digest}"


def allowed_values(field: dict[str, Any]) -> list[str]:
    raw = field.get("allowed_values")
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(value) for value in raw]
    return [value.strip() for value in str(raw).split(",") if value.strip()]


def default_arguments(field: dict[str, Any]) -> list[str]:
    raw_default = field.get("default")
    default = str(raw_default)
    name = field["name"]
    arguments: list[str] = []
    if isinstance(raw_default, list):
        arguments.append("default=list")
    elif isinstance(raw_default, dict):
        arguments.append(
            "default=default_accepted_selection"
            if raw_default == {"choices": [], "unresolved_keys": []}
            else "default=dict"
        )
    elif default in {"transaction timestamp at insertion", "transaction timestamp"}:
        arguments.append("auto_now_add=True")
    elif name == "updated_at" and default == "now":
        arguments.append("auto_now=True")
    elif default == "now":
        arguments.append("default=timezone.now")
    elif default in {"uuid4", "uuid4 for new records; preserve original UUID during migration", "uuid4 for the first version; reuse for corrections", "uuid4 for first version; reuse for corrections"}:
        arguments.append("default=uuid.uuid4")
    elif default in {"empty array", "[]"}:
        arguments.append("default=list")
    elif default == "empty object":
        arguments.append("default=dict")
    elif default == '{"choices":[],"unresolved_keys":[]}':
        arguments.append("default=default_accepted_selection")
    elif default == "empty string":
        arguments.extend(['default=""', "blank=True"])
    elif default == "true":
        arguments.append("default=True")
    elif default == "false":
        arguments.append("default=False")
    elif re.fullmatch(r"-?\d+", default):
        arguments.append(f"default={default}")
    elif default not in {"none", "NULL", "None", "derived"}:
        arguments.append(f"default={default!r}")
    if not field["required"]:
        arguments.extend(["null=True", "blank=True"])
    return arguments


def required_numeric_size(field_type: str) -> int:
    match = re.search(r"\d+", field_type)
    if match is None:
        raise ValueError(f"Field type has no numeric size: {field_type}")
    return int(match.group())


def field_source(entity: dict[str, Any], field: dict[str, Any]) -> tuple[str, str]:
    name = field["name"]
    field_type = field["type"]
    attribute = name[:-3] if field_type.startswith("fk:") and name.endswith("_id") else name
    arguments = default_arguments(field)
    if name == "id":
        return name, "models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)"
    if field_type.startswith("fk:"):
        target = field_type.split(":", 1)[1]
        reference = "settings.AUTH_USER_MODEL" if target == "Account" else repr("self" if target == entity["entity"] else target)
        arguments = [reference, "on_delete=models.PROTECT", 'related_name="+"', *arguments]
        return attribute, f"models.ForeignKey({', '.join(arguments)})"
    if field_type.startswith("json:"):
        contract = field_type.split(":", 1)[1]
        return name, f"ValidatedJSONField(contract={contract!r}{', ' if arguments else ''}{', '.join(arguments)})"
    if field_type.startswith("encrypted_varchar"):
        maximum = required_numeric_size(field_type)
        return name, f"EncryptedCharField(max_length={maximum}{', ' if arguments else ''}{', '.join(arguments)})"
    if (entity["entity"], name) in ENCRYPTED_FIELDS:
        if field_type.startswith("varchar"):
            maximum = required_numeric_size(field_type)
            return name, f"EncryptedCharField(max_length={maximum}{', ' if arguments else ''}{', '.join(arguments)})"
        return name, f"EncryptedTextField({', '.join(arguments)})"
    if field_type == "uuid":
        constructor = "models.UUIDField"
    elif field_type in {"instant", "timestamptz"}:
        constructor = "models.DateTimeField"
    elif field_type == "date":
        constructor = "models.DateField"
    elif field_type == "daterange":
        constructor = "DateRangeField"
    elif field_type == "boolean":
        constructor = "models.BooleanField"
    elif field_type == "bigint":
        constructor = "models.BigIntegerField"
    elif field_type == "integer":
        constructor = "models.IntegerField"
    elif field_type == "positive_integer":
        constructor = "models.PositiveIntegerField"
    elif field_type == "smallint":
        constructor = "models.SmallIntegerField"
    elif field_type == "text":
        constructor = "models.TextField"
    elif field_type == "tsvector":
        constructor = "SearchVectorField"
    elif field_type.startswith("vector("):
        constructor = "VectorField"
        arguments.insert(0, f"dimensions={required_numeric_size(field_type)}")
    elif field_type == "enum":
        values = allowed_values(field)
        arguments.insert(0, f"max_length={max(16, *(len(value) for value in values))}")
        arguments.insert(1, f"choices={[(value, value) for value in values]!r}")
        constructor = "models.CharField"
    elif field_type.startswith("varchar") or field_type.startswith("char"):
        maximum = required_numeric_size(field_type)
        arguments.insert(0, f"max_length={maximum}")
        constructor = "models.CharField"
    else:
        raise ValueError(f"Unsupported field type {field_type} on {entity['entity']}.{name}")
    return attribute, f"{constructor}({', '.join(arguments)})"


def meta_source(entity: dict[str, Any]) -> list[str]:
    name = entity["entity"]
    constraints: list[str] = []
    if any(field["name"] == "owner_id" and field["required"] for field in entity["fields"]):
        constraints.append(
            f"models.UniqueConstraint(fields=['id', 'owner'], name={safe_name(name, 'id_owner_uq')!r})"
        )
    for index, (fields, condition, nulls_not_distinct) in enumerate(UNIQUE_FIELDS.get(name, []), 1):
        options = [f"fields={fields!r}", f"name={safe_name(name, f'uq_{index}')!r}"]
        if condition:
            options.append(f"condition={condition}")
        if nulls_not_distinct:
            options.append("nulls_distinct=False")
        constraints.append(f"models.UniqueConstraint({', '.join(options)})")
    for index, condition in enumerate(CHECKS.get(name, []), 1):
        constraints.append(
            f"models.CheckConstraint(condition={condition}, name={safe_name(name, f'ck_{index}')!r})"
        )
    indexes: list[str] = []
    for index, (kind, fields) in enumerate(INDEXES.get(name, []), 1):
        index_name = safe_index_name(name, f"ix_{index}")
        if kind == "gin":
            indexes.append(f"GinIndex(fields={fields!r}, name={index_name!r})")
        elif kind == "hnsw":
            indexes.append(
                f"HnswIndex(fields={fields!r}, name={index_name!r}, m=16, ef_construction=64, opclasses=['vector_cosine_ops'])"
            )
        else:
            indexes.append(f"models.Index(fields={fields!r}, name={index_name!r})")
    result = ["    class Meta:", f"        db_table = 'adviser_v2_{snake(name)}'"]
    if constraints:
        result.append("        constraints = [")
        result.extend(f"            {constraint}," for constraint in constraints)
        result.append("        ]")
    if indexes:
        result.append("        indexes = [")
        result.extend(f"            {index}," for index in indexes)
        result.append("        ]")
    return result


def module_source(entities: list[dict[str, Any]]) -> str:
    lines = [
        '"""Generated from research/design/entity-field-dictionary.json (discussion-r25-final-review)."""',
        "",
        "from __future__ import annotations",
        "",
        "import uuid",
        "",
        "from django.conf import settings",
        "from django.contrib.postgres.fields import DateRangeField",
        "from django.contrib.postgres.indexes import GinIndex",
        "from django.contrib.postgres.search import SearchVectorField",
        "from django.db import models",
        "from django.db.models import F, Q",
        "from django.utils import timezone",
        "from pgvector.django import HnswIndex, VectorField",
        "",
        "from ..fields import EncryptedCharField, EncryptedTextField, ValidatedJSONField",
        "from .base import ApprovedModel, default_accepted_selection",
        "",
    ]
    for entity in entities:
        lines.extend(
            [
                f"class {entity['entity']}(ApprovedModel):",
                f"    {entity['purpose']!r}",
            ]
        )
        for field in entity["fields"]:
            attribute, source = field_source(entity, field)
            lines.append(f"    {attribute} = {source}")
        lines.append("")
        lines.extend(meta_source(entity))
        lines.extend(["", ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    document = json.loads(SOURCE.read_text(encoding="utf-8"))
    entities = {entity["entity"]: entity for entity in document["entities"]}
    if document["revision"] != "discussion-r25-final-review" or len(entities) != 62:
        raise RuntimeError("The approved design authority changed; review before regenerating.")
    expected = set().union(*GROUPS.values())
    actual = set(entities) - {"Account"}
    if expected != actual:
        raise RuntimeError(f"Model grouping drift: missing={actual - expected}, extra={expected - actual}")
    for entity_name, unique_constraints in UNIQUE_FIELDS.items():
        available = {
            field["name"][:-3]
            if field["type"].startswith("fk:") and field["name"].endswith("_id")
            else field["name"]
            for field in entities[entity_name]["fields"]
        }
        referenced = {name for fields, _, _ in unique_constraints for name in fields}
        if referenced - available:
            raise RuntimeError(
                f"Invalid unique fields for {entity_name}: {sorted(referenced - available)}"
            )
    for entity_name, indexes in INDEXES.items():
        available = {
            field["name"][:-3]
            if field["type"].startswith("fk:") and field["name"].endswith("_id")
            else field["name"]
            for field in entities[entity_name]["fields"]
        }
        referenced = {name.removeprefix("-") for _, fields in indexes for name in fields}
        if referenced - available:
            raise RuntimeError(
                f"Invalid index fields for {entity_name}: {sorted(referenced - available)}"
            )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for module, names in GROUPS.items():
        ordered = [entity for entity in document["entities"] if entity["entity"] in names]
        (OUTPUT / f"{module}.py").write_text(module_source(ordered), encoding="utf-8")


if __name__ == "__main__":
    main()
