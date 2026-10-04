"""Synthetic A–E journeys: every customer change enters through a chat turn."""

import time
import uuid
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.adviser_v2.demo.chat_services import commit_turn, start
from apps.adviser_v2.demo.evidence import atomic_json
from apps.adviser_v2.models import DemoRelease

PROFILES = {
    "A": {
        "people": "Myself, age 35, my spouse age 33, and our dependent child age 8. We live in Pune.",
        "needs": "Room limits and maternity cover matter to me.",
        "strength": {"room_limit": "Nice-to-have", "maternity": "Must-have"},
    },
    "B": {
        "people": "Myself age 70 and my spouse age 67. We live in Pune.",
        "needs": "Low co-pay is a nice-to-have.",
        "strength": {"copay": "Nice-to-have"},
    },
    "C": {
        "people": "Myself age 29 and my spouse age 28. We live in Pune.",
        "needs": "Maternity cover is a must-have.",
        "strength": {"maternity": "Must-have"},
    },
    "D": {
        "people": "Myself age 45, my spouse age 43, our dependent child age 12, and my parent age 72. We live in Pune.",
        "needs": "My parent needs OPD cover; that is a must-have.",
        "strength": {"opd": "Must-have"},
    },
    # A pasted demo chat: one person, a state after the city, option and
    # glossary questions, then a request for plans in the middle of narrowing.
    "E": {
        "script": {
            "people": ["just for me"],
            "age": ["35 years"],
            "city": ["kota, rajasthan"],
            "sum_insured": [
                "can you provide option in what sum insured is available and would be more suitable for me"
            ],
            "annual_budget": ["I don't have any budget"],
            "needs": ["can you explain me in detail, what does these even mean?", "Skip"],
            "health_details": ["I don't have any PED"],
            "narrow": ["no", "no", "no. Can you suggest me plans now"],
            "batch": ["next five", "next five", "next five"],
        },
        "strength": {},
    },
}


def turn_groups(data):
    """Retain the complete check trail at every committed profile revision."""
    cards = {c["plan_id"]: c for c in data["cards"]}
    return {
        group: [
            {
                **item,
                "policy_version_id": item["plan_id"],
                "variant": cards[item["plan_id"]]["variant"],
                "insurer": cards[item["plan_id"]]["insurer"],
                "name": cards[item["plan_id"]]["name"],
                "card_version": cards[item["plan_id"]].get("card_version"),
                "deciding_checks": [
                    r
                    for r in item["hard_limits"]
                    if r["status"]
                    == (
                        "doesnt_fit"
                        if group == "doesnt_fit"
                        else "unresolved"
                        if group == "unresolved"
                        else "fits"
                    )
                ],
            }
            for item in items
        ]
        for group, items in data["state"]["fit_groups"].items()
    }


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--run-id", required=True)
        parser.add_argument("--release-id")

    def handle(self, **options):
        if settings.DATABASES["default"]["NAME"] != "coverguide_star_slice":
            raise CommandError("Local synthetic profiles only.")
        release = (
            DemoRelease.objects.get(pk=options["release_id"])
            if options["release_id"]
            else DemoRelease.objects.get(active=True)
        )
        if not release.fact_cards.exists():
            raise CommandError("Publish the priority immutable-card release first.")
        output = (
            Path(settings.BASE_DIR).parent
            / "output"
            / ("section16-profiles-" + options["run_id"] + ".json")
        )
        if output.exists():
            raise CommandError("Use a fresh run ID; do not overwrite measured conversations.")
        user, _ = User.objects.get_or_create(
            email="section16-profiles@example.invalid", defaults={"is_active": True}
        )
        results = []
        for name, spec in PROFILES.items():
            started = time.monotonic()
            data = start(user, release_id=release.id)
            turns = []
            initial = data["state"]
            turns.append(
                {
                    "turn": 0,
                    "customer": None,
                    "assistant": initial["message"],
                    "stage": initial["stage"],
                    "counts": {k: len(v) for k, v in initial["fit_groups"].items()},
                    "elapsed_ms": round((time.monotonic() - started) * 1000),
                    "groups": turn_groups(data),
                    "questions_asked": 1,
                    "pending": initial["pending"],
                }
            )
            script = {k: list(v) for k, v in spec.get("script", {}).items()}
            needs_sent = bool(script)
            for n in range(20):
                state = data["state"]
                pending = state["pending"]
                field = pending["field"] if pending else ""
                if state["stage"] == "narrowing" and state["stop_reason"] and needs_sent:
                    break
                if script:
                    queue = script.get(pending["template"] if pending else "") or script.get(field)
                    if not pending or pending["template"] == "exhausted":
                        break
                    message = queue.pop(0) if queue else "Skip"
                elif state["stage"] == "narrowing" and not needs_sent:
                    # Supply the same profile needs through chat even if a
                    # volunteered earlier preference skipped the open prompt.
                    message = spec["needs"]
                    needs_sent = True
                elif field == "people":
                    message = spec["people"]
                elif field == "city":
                    message = "Pune"
                elif field == "sum_insured":
                    message = "10 lakh rupees sum insured."
                elif field == "annual_budget":
                    message = "My annual premium budget is 60000 rupees."
                elif field == "coverage_basis":
                    message = "One shared cover for all of us, a family floater."
                elif field in {"plan_type", "cover_need"}:
                    message = "I want medical indemnity cover for hospital expenses, on a family floater basis."
                elif field == "health_details":
                    message = "Skip"
                elif field == "needs":
                    message = spec["needs"]
                    needs_sent = True
                elif pending["template"] == "strength":
                    message = spec["strength"].get(field, "Nice-to-have")
                elif pending["template"] == "narrow":
                    message = "Skip"
                else:
                    message = "Skip"
                before = state["question_count"]
                tick = time.monotonic()
                data = commit_turn(
                    user,
                    data["id"],
                    request_id=uuid.uuid4(),
                    revision=state["revision"],
                    text=message,
                    dispatch=False,
                )
                state = data["state"]
                turns.append(
                    {
                        "turn": n + 1,
                        "customer": message,
                        "assistant": state["message"],
                        "stage": state["stage"],
                        "counts": {k: len(v) for k, v in state["fit_groups"].items()},
                        "elapsed_ms": round((time.monotonic() - tick) * 1000),
                        "service_elapsed_ms": state["turns"][-1]["elapsed_ms"],
                        "groups": turn_groups(data),
                        "questions_asked": state["question_count"] - before,
                        "pending": state["pending"],
                        "model": state["turns"][-1]["model"],
                        "stop_reason": state["stop_reason"],
                    }
                )
                self.stdout.write(
                    f"{name} turn {n + 1}: {state['stage']} {turns[-1]['counts']} {turns[-1]['elapsed_ms']} ms"
                )
                self.stdout.flush()
            results.append(
                {
                    "profile": name,
                    "conversation_id": data["id"],
                    "release_id": data["release_id"],
                    "turns": turns,
                    "total_question_count": data["state"]["question_count"],
                    "stop_reason": data["state"]["stop_reason"],
                    "total_ms": round((time.monotonic() - started) * 1000),
                    "final_profile": data["state"]["profile"],
                    "intended_needs": spec["strength"],
                    "needs_delivered": needs_sent,
                    "needs_classified_as_intended": all(
                        any(
                            r["field"] == field
                            and r["strength"]
                            == ("must_have" if strength == "Must-have" else "nice_to_have")
                            for r in data["state"]["profile"]["requirements"]
                        )
                        for field, strength in spec["strength"].items()
                    ),
                    "fit_groups": data["state"]["fit_groups"],
                    "card_versions": [c.get("card_version") for c in data["cards"]],
                }
            )
            atomic_json(
                output,
                {
                    "schema_version": 2,
                    "synthetic": True,
                    "run_id": options["run_id"],
                    "profiles": results,
                },
            )
        self.stdout.write(str(output))
