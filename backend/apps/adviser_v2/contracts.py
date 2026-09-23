"""The approved closed database JSON contracts.

Pydantic establishes the JSON value boundary and one named RootModel per contract;
the approved draft-2020-12 schema performs the nested closed-world validation. This
keeps the executable contract byte-for-byte aligned with the reviewed design instead
of maintaining a second handwritten interpretation.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, ClassVar, cast

from jsonschema import Draft202012Validator, FormatChecker
from pydantic import JsonValue, RootModel, model_validator

SCHEMA_PATH = Path(__file__).with_name("database-json-contracts-r26.json")
COMPONENT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "design"
    / "history"
    / "discussion-r17-before-batch11-approval"
    / "json-contracts.schema.json"
)
REQUIRED_COMPONENTS = frozenset(
    {
        "BoundingBoxV1",
        "BundleConsequenceV1",
        "ComponentScopeV1",
        "DurationV1",
        "LimitScopeV1",
        "PredicateV1",
        "StringListV1",
        "TableAxesV1",
    }
)


@lru_cache(maxsize=1)
def contract_document() -> dict[str, Any]:
    document = cast(dict[str, Any], json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    definitions = document.get("$defs", {})
    missing = REQUIRED_COMPONENTS - definitions.keys()
    if missing:
        # The final r25 export accidentally omitted its closed helper definitions.
        # R17 is the last reviewed snapshot containing them; later contracts retain
        # byte-identical references to these names. Merge helpers only, never an
        # older database-field contract.
        component_document = cast(
            dict[str, Any], json.loads(COMPONENT_SCHEMA_PATH.read_text(encoding="utf-8"))
        )
        component_definitions = component_document.get("$defs", {})
        unavailable = missing - component_definitions.keys()
        if unavailable:
            names = ", ".join(sorted(unavailable))
            raise LookupError(f"Missing approved JSON component definitions: {names}")
        definitions.update({name: component_definitions[name] for name in missing})
    # R17's BoundingBoxV1 used one prefix item together with ``items: false``,
    # making its simultaneous four-item requirement unsatisfiable. The prose
    # contract is an exact four-number PDF rectangle.
    definitions["BoundingBoxV1"] = {
        "type": "array",
        "items": {"type": "number", "minimum": 0},
        "minItems": 4,
        "maxItems": 4,
    }
    Draft202012Validator.check_schema(document)
    return document


@lru_cache(maxsize=64)
def contract_validator(name: str) -> Draft202012Validator:
    document = contract_document()
    definitions = document.get("$defs", {})
    if name not in definitions:
        raise LookupError(f"Unknown CoverGuide JSON contract: {name}")
    return Draft202012Validator(
        {
            "$schema": document["$schema"],
            "$ref": f"#/$defs/{name}",
            "$defs": definitions,
        },
        format_checker=FormatChecker(),
    )


def contract_schema_document(name: str) -> dict[str, Any]:
    """Return one contract plus its complete transitive local-reference closure."""

    document = contract_document()
    definitions = document["$defs"]
    if name not in definitions:
        raise LookupError(f"Unknown CoverGuide JSON contract: {name}")
    selected: dict[str, Any] = {}
    pending = [name]
    while pending:
        current = pending.pop()
        if current in selected:
            continue
        definition = definitions[current]
        selected[current] = definition
        references = _contract_references(definition)
        unavailable = references - definitions.keys()
        if unavailable:
            raise LookupError(
                "Missing referenced CoverGuide contracts: " + ", ".join(sorted(unavailable))
            )
        pending.extend(sorted(references - selected.keys()))
    return {
        "$schema": document["$schema"],
        "$ref": f"#/$defs/{name}",
        "$defs": selected,
    }


def _contract_references(value: object) -> set[str]:
    references: set[str] = set()
    if isinstance(value, dict):
        reference = value.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/$defs/"):
            references.add(reference.removeprefix("#/$defs/"))
        for child in value.values():
            references.update(_contract_references(child))
    elif isinstance(value, list):
        for child in value:
            references.update(_contract_references(child))
    return references


class ClosedContract(RootModel[JsonValue]):
    contract_name: ClassVar[str]

    @model_validator(mode="after")
    def validate_approved_schema(self) -> ClosedContract:
        errors = sorted(
            contract_validator(self.contract_name).iter_errors(self.root),
            key=lambda item: tuple(str(part) for part in item.absolute_path),
        )
        if errors:
            error = errors[0]
            path = ".".join(str(part) for part in error.absolute_path) or "$"
            raise ValueError(f"{self.contract_name} at {path}: {error.message}")
        return self


class AcceptedSelectionV1(ClosedContract):
    contract_name = "AcceptedSelectionV1"


class ApplicabilityV1(ClosedContract):
    contract_name = "ApplicabilityV1"


class AssumptionsV1(ClosedContract):
    contract_name = "AssumptionsV1"


class AuditMetadataV1(ClosedContract):
    contract_name = "AuditMetadataV1"


class CalculationInputsV1(ClosedContract):
    contract_name = "CalculationInputsV1"


class CalculationOperationsV1(ClosedContract):
    contract_name = "CalculationOperationsV1"


class CapabilityScopeV1(ClosedContract):
    contract_name = "CapabilityScopeV1"


class ConfigurationV1(ClosedContract):
    contract_name = "ConfigurationV1"


class CustomerPolicyFactValueV1(ClosedContract):
    contract_name = "CustomerPolicyFactValueV1"


class CustomerPolicySelectionV1(ClosedContract):
    contract_name = "CustomerPolicySelectionV1"


class DeletionScopeV1(ClosedContract):
    contract_name = "DeletionScopeV1"


class DeletionVerificationV1(ClosedContract):
    contract_name = "DeletionVerificationV1"


class EvidenceContextV1(ClosedContract):
    contract_name = "EvidenceContextV1"


class ExpressionV1(ClosedContract):
    contract_name = "ExpressionV1"


class FactValueV1(ClosedContract):
    contract_name = "FactValueV1"


class IdentifiersV1(ClosedContract):
    contract_name = "IdentifiersV1"


class NetworkRestrictionsV1(ClosedContract):
    contract_name = "NetworkRestrictionsV1"


class OriginalLocatorV1(ClosedContract):
    contract_name = "OriginalLocatorV1"


class ProcessingIssuesV1(ClosedContract):
    contract_name = "ProcessingIssuesV1"


class ProviderNetworkScopeV1(ClosedContract):
    contract_name = "ProviderNetworkScopeV1"


class QualificationV1(ClosedContract):
    contract_name = "QualificationV1"


class QuantityV1(ClosedContract):
    contract_name = "QuantityV1"


class QuotePaymentScheduleV1(ClosedContract):
    contract_name = "QuotePaymentScheduleV1"


class QuotePriceBreakdownV1(ClosedContract):
    contract_name = "QuotePriceBreakdownV1"


class RuleV1(ClosedContract):
    contract_name = "RuleV1"


class TableSelectorsV1(ClosedContract):
    contract_name = "TableSelectorsV1"


class TemporalExtentV1(ClosedContract):
    contract_name = "TemporalExtentV1"


class TurnEventV1(ClosedContract):
    contract_name = "TurnEventV1"


class TypedValueV1(ClosedContract):
    contract_name = "TypedValueV1"


class UsageV1(ClosedContract):
    contract_name = "UsageV1"


class UuidListV1(ClosedContract):
    contract_name = "UuidListV1"


CONTRACT_TYPES: dict[str, type[ClosedContract]] = {
    model.contract_name: model for model in ClosedContract.__subclasses__()
}


def validate_contract(name: str, value: Any) -> JsonValue:
    try:
        model = CONTRACT_TYPES[name]
    except KeyError as exc:
        raise LookupError(f"Unknown CoverGuide JSON contract: {name}") from exc
    return model.model_validate(value).root
