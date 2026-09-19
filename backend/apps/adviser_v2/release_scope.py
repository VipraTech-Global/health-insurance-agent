"""Fail-closed release-size rules for normal and restricted demo releases."""

from __future__ import annotations

from typing import Protocol

FIVE_PRODUCT_COUNT = 5
THREE_PRODUCT_DEMO_COUNT = 3
STANDARD_RELEASE_LABEL = "development_alpha"
THREE_PRODUCT_DEMO_LABEL = "development_alpha_3_product"


class ReleaseScope(Protocol):
    release_label: str
    readiness: dict[str, object]


def comparison_product_count(release: ReleaseScope) -> int:
    """Return the committed comparison size or reject inconsistent metadata."""

    value = release.readiness.get("comparison_product_count", FIVE_PRODUCT_COUNT)
    demo_subset = release.readiness.get("demo_subset", False)
    if (
        release.release_label == THREE_PRODUCT_DEMO_LABEL
        and value == THREE_PRODUCT_DEMO_COUNT
        and demo_subset is True
    ):
        return THREE_PRODUCT_DEMO_COUNT
    if (
        release.release_label == STANDARD_RELEASE_LABEL
        and value == FIVE_PRODUCT_COUNT
        and demo_subset is not True
    ):
        return FIVE_PRODUCT_COUNT
    raise ValueError("Knowledge release has inconsistent product-count metadata.")
