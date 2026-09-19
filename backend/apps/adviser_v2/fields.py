"""Database fields enforcing approved encryption and JSON contracts on every write."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models

from .contracts import validate_contract
from .crypto import decrypt_text, encrypt_text


class ValidatedJSONField(models.JSONField):
    def __init__(self, *args: Any, contract: str, **kwargs: Any) -> None:
        self.contract = contract
        super().__init__(*args, **kwargs)

    def deconstruct(self) -> tuple[str, str, Sequence[Any], dict[str, Any]]:
        name, path, args, kwargs = super().deconstruct()
        kwargs["contract"] = self.contract
        return name, path, args, kwargs

    def get_prep_value(self, value: Any) -> Any:
        if value is None and self.null:
            return None
        try:
            value = validate_contract(self.contract, value)
        except (LookupError, ValueError) as exc:
            raise ValidationError(str(exc), code="invalid_json_contract") from exc
        return super().get_prep_value(value)

    def validate(self, value: Any, model_instance: models.Model | None) -> None:
        super().validate(value, model_instance)
        try:
            validate_contract(self.contract, value)
        except (LookupError, ValueError) as exc:
            raise ValidationError(str(exc), code="invalid_json_contract") from exc


class EncryptedTextField(models.TextField):  # type: ignore[type-arg]
    description = "AES-256-GCM encrypted text"

    @property
    def associated_data(self) -> bytes:
        return f"{self.model._meta.label_lower}:{self.name}".encode()

    def from_db_value(self, value: Any, expression: Any, connection: Any) -> str | None:
        if value is None:
            return None
        return decrypt_text(str(value), associated_data=self.associated_data)

    def to_python(self, value: Any) -> str | None:
        if value is None or isinstance(value, str) and not value.startswith("cg2$"):
            return value
        return decrypt_text(str(value), associated_data=self.associated_data)

    def get_prep_value(self, value: Any) -> str | None:
        value = super().get_prep_value(value)
        if value is None:
            return None
        return encrypt_text(str(value), associated_data=self.associated_data)


class EncryptedCharField(EncryptedTextField):
    def __init__(self, *args: Any, max_length: int, **kwargs: Any) -> None:
        self.plaintext_max_length = max_length
        kwargs.pop("max_length", None)
        kwargs["max_length"] = max_length
        super().__init__(*args, **kwargs)

    def deconstruct(self) -> tuple[str, str, Sequence[Any], dict[str, Any]]:
        name, path, args, kwargs = super().deconstruct()
        kwargs["max_length"] = self.plaintext_max_length
        return name, path, args, kwargs

    def validate(self, value: Any, model_instance: models.Model | None) -> None:
        if value is not None and len(str(value)) > self.plaintext_max_length:
            raise ValidationError(
                f"Ensure this value has at most {self.plaintext_max_length} characters.",
                code="max_length",
            )
        super().validate(value, model_instance)
