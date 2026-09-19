from __future__ import annotations

from collections.abc import Collection
from typing import Any, Self

from django.core.exceptions import ValidationError
from django.db import models


def default_accepted_selection() -> dict[str, list[object]]:
    return {"choices": [], "unresolved_keys": []}


class ApprovedModel(models.Model):
    """Common immutability guard for approved identities and private ownership."""

    _loaded_identity: tuple[object, object] | None = None

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self._loaded_identity is not None:
            loaded_id, loaded_owner = self._loaded_identity
            if loaded_id != getattr(self, "id", None):
                raise ValidationError("Stable row IDs are immutable.")
            if hasattr(self, "owner_id") and loaded_owner != getattr(self, "owner_id", None):
                raise ValidationError("Row ownership is immutable.")
        super().save(*args, **kwargs)
        self._loaded_identity = (
            getattr(self, "id", None),
            getattr(self, "owner_id", None),
        )

    @classmethod
    def from_db(cls, db: str | None, field_names: Collection[str], values: Collection[Any]) -> Self:
        instance = super().from_db(db, field_names, values)
        instance._loaded_identity = (
            getattr(instance, "id", None),
            getattr(instance, "owner_id", None),
        )
        return instance
