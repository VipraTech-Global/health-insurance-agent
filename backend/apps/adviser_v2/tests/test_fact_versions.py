import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction

from apps.adviser_v2.demo.chat_services import release_cards, start
from apps.adviser_v2.demo.citations import card_anchor
from apps.adviser_v2.demo.contracts import Citation
from apps.adviser_v2.demo.fact_rules import ExecutableRule, project
from apps.adviser_v2.models import DemoFactCard, DemoRelease
from apps.adviser_v2.tests.test_demo_contracts import citation, packet
from apps.adviser_v2.tests.test_demo_services import demo  # noqa: F401


def answer(text):
    from apps.adviser_v2.demo.contracts import Statement

    return {
        "status": "answered",
        "answer": {"statements": [Statement(text=text, citations=[citation(text)]).model_dump()]},
    }


def test_rule_types_reject_unbounded_inputs_and_preserve_inclusive_printed_age():
    with pytest.raises(ValueError):
        ExecutableRule(field="entry_age", kind="age", minimum=18, citations=[citation()])
    with pytest.raises(ValueError):
        ExecutableRule(
            field="entry_age",
            kind="age",
            minimum=65,
            maximum=18,
            unit="years",
            citations=[citation()],
        )
    with pytest.raises(ValueError):
        ExecutableRule(
            field="copay",
            kind="maximum",
            value="perhaps 10",
            unit="percent",
            citations=[citation()],
        )
    rules, legacy = project(
        "entry_age",
        answer("Any person aged between 18 years and 65 years can take this insurance."),
        "Default",
    )
    assert (
        rules[0]["minimum"] == 18
        and rules[0]["maximum"] == 65
        and rules[0]["unit"] == "years"
        and rules[0]["inclusive"]
    )
    assert legacy["entry_ages"][0]["maximum_days"] == 66 * 365 - 1


def test_quoted_does_not_imply_executable_optional_or_conditional_cover():
    for raw in [
        "Maternity is covered subject to a 24 month waiting period.",
        "Maternity is covered only under an optional cover.",
        "Maternity may be covered.",
    ]:
        rules, _ = project("maternity", answer(raw), "Default")
        assert not rules
    yes, _ = project("maternity", answer("Maternity is covered."), "Default")
    no, _ = project("maternity", answer("Maternity is not covered."), "Default")
    assert yes[0]["value"] == "covered" and no[0]["value"] == "not_covered"
    mixed = answer("Maternity is covered.")
    mixed["answer"]["statements"].extend(
        answer("Maternity is not covered.")["answer"]["statements"]
    )
    assert project("maternity", mixed, "Default")[0] == []


def test_territory_does_not_become_purchase_geography_and_basis_not_product_type():
    assert project("geography", answer("Treatment is covered in India."), "Default")[0] == []
    basis, _ = project(
        "coverage_basis",
        answer("The policy is available on individual and floater basis."),
        "Default",
    )
    assert basis[0]["value"] == "individual|floater"
    assert (
        project(
            "plan_type",
            answer("The policy is available on individual and floater basis."),
            "Default",
        )[0]
        == []
    )


@pytest.mark.django_db(transaction=True)
def test_cards_are_immutable_in_model_and_database_and_old_release_remains_pinned(v2_user, demo):  # noqa: F811
    release, _, indexes = demo
    old = DemoFactCard.objects.create(
        id="1" * 64, index=indexes[0], card=indexes[0].card, audit_path="old"
    )
    release.fact_cards.add(old)
    session = start(v2_user)
    old.card = {"replaced": True}
    with pytest.raises(ValidationError):
        old.save()
    with pytest.raises(DatabaseError), transaction.atomic():
        DemoFactCard.objects.filter(pk=old.pk).update(card={"replaced": True})
    replacement = DemoFactCard.objects.create(
        id="2" * 64, index=indexes[0], card={**indexes[0].card, "model": "new"}, audit_path="new"
    )
    release.active = False
    release.save()
    newer = DemoRelease.objects.create(
        method="H", manifest_sha256="c" * 64, bakeoff={}, active=True
    )
    newer.indexes.add(indexes[0])
    newer.fact_cards.add(replacement)
    assert session["release_id"] == str(release.id)
    assert release_cards(release)[0]["card_version"] == old.id
    assert release_cards(newer)[0]["card_version"] == replacement.id


def test_card_citation_replacement_cannot_resolve_a_quote_missing_from_old_card():
    source = packet("Old printed cover. New printed cover.")
    bundle = {"sections": [source.sections[0].payload()]}
    old = {
        "plan_id": "plan",
        "citations": [
            Citation(section_id="s", page_id="p", quote="Old printed cover.").model_dump()
        ],
    }
    foreign = Citation(section_id="s", page_id="p", quote="New printed cover.")
    with pytest.raises(ValueError):
        card_anchor(old, bundle, foreign)
