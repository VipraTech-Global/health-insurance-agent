"""Pin published fact cards to a plan's re-read index edition without repeating AI calls.

Re-reading a plan's tables gives its index a new id while the section text stays the
same, so its card and price quotations are unchanged. A card is carried only when every
quotation opens at the same source position in the new edition; other cards are kept.
"""

import hashlib
import json
from functools import partial
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.adviser_v2.demo.charts import load_prices
from apps.adviser_v2.demo.citations import card_anchor, price_anchor, published_citations
from apps.adviser_v2.demo.contracts import Citation
from apps.adviser_v2.demo.evidence import atomic_json, digest
from apps.adviser_v2.demo.fact_cards_v3 import freeze_prices
from apps.adviser_v2.demo.premium_sources import priced_bundle
from apps.adviser_v2.demo.price_compare import load_chart
from apps.adviser_v2.demo.pricing import validate_price
from apps.adviser_v2.demo.services import bundle_for
from apps.adviser_v2.models import DemoFactCard, DemoPlanIndex


def replaced(value, old, new):
    """The value with every exact occurrence of the old index id changed to the new one."""
    if isinstance(value, dict):
        return {replaced(k, old, new): replaced(v, old, new) for k, v in value.items()}
    if isinstance(value, list):
        return [replaced(v, old, new) for v in value]
    return new if value == old else value


def price_quotes(chart):
    """The quotations a chart publishes, or None when it has no fully validated price
    (such a chart shows no prices, and is carried as it is)."""
    prices, cells = load_prices(chart)
    if not prices or any(
        not validate_price(price, cells, set(chart["required_axes"])) for price in prices
    ):
        return None
    keys = {k for p in prices for k in [p.value_cell, *p.axis_cells.values(), *p.heading_cells]}
    zones = [Citation.model_validate(c) for z in chart.get("zone_lists", []) for c in z["zones"]]
    return unique([cells[k].citation for k in sorted(keys)] + zones)


def unique(quotes):
    return list({q.model_dump_json(): q for q in quotes}.values())


def quote_anchor(plan, bundle, quote):
    """Where a validated chart quotation opens: price_anchor's final step, without
    revalidating every price for each quotation."""
    return card_anchor({"plan_id": plan, "citations": [quote.model_dump()]}, bundle, quote)


def same_anchors(name, quotes, before, after):
    for quote in quotes:
        try:
            moved = after(quote) == before(quote)
        except ValueError as exc:
            raise CommandError(f"{name}: {quote.quote[:60]!r} no longer opens: {exc}") from exc
        if not moved:
            raise CommandError(f"{name}: {quote.quote[:60]!r} opens elsewhere in the new edition.")


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--source-run", required=True)
        parser.add_argument("--run-id", required=True)
        parser.add_argument(
            "--index",
            action="append",
            required=True,
            help="A re-read index id; the source card for the same plan and variant moves to it.",
        )

    def handle(self, **options):
        if settings.DATABASES["default"]["NAME"] != "coverguide_star_slice":
            raise CommandError("Isolated local cards only.")
        report = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
        source = report / "fact-card-runs" / options["source_run"]
        target = report / "fact-card-runs" / options["run_id"]
        if not (source / "complete.json").exists():
            raise CommandError("The source card run is not complete.")
        saved = json.loads((source / "complete.json").read_text())
        if saved.get("failures"):
            raise CommandError("Resolve the source run's pending cards first.")
        cards = {
            c.id: c
            for c in DemoFactCard.objects.select_related("index").filter(
                pk__in=[r["id"] for r in saved["cards"]]
            )
        }
        if len(cards) != len(saved["cards"]):
            raise CommandError("The source run names cards that do not exist.")
        moves = {}
        for index in DemoPlanIndex.objects.filter(pk__in=options["index"]):
            old = [
                c
                for c in cards.values()
                if (c.index.plan_key, c.index.variant) == (index.plan_key, index.variant)
            ]
            if len(old) != 1 or old[0].index_id == index.id:
                raise CommandError(f"{index.id}: no other source card for this plan and variant.")
            moves[old[0].id] = index
        if len(moves) != len(set(options["index"])):
            raise CommandError("Unknown index id.")
        manifest = {
            "schema_version": 1,
            "run_id": options["run_id"],
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "source_run": options["source_run"],
            "source_manifest": saved["manifest"],
            "carried": {cards[k].index_id: i.id for k, i in sorted(moves.items())},
        }
        if (target / "manifest.json").exists() and json.loads(
            (target / "manifest.json").read_text()
        ) != manifest:
            raise CommandError("This run was made differently; create a fresh versioned run.")
        (target / "cards").mkdir(parents=True, exist_ok=True)
        atomic_json(target / "manifest.json", manifest)
        completed, report_rows = [], []
        for item in saved["cards"]:
            old = cards[item["id"]]
            index = moves.get(old.id)
            if index is None:
                completed.append(item)
                continue
            name = f"{old.index.name} ({old.index.variant})"
            card = {
                k: v
                for k, v in old.card.items()
                if k not in ("card_version", "pricing_artifact", "pricing_sha256")
            }
            card["index_version"] = index.id
            quotes = unique(published_citations(old.card))
            before, after = bundle_for(old.index), bundle_for(index)
            same_anchors(
                name,
                quotes,
                partial(card_anchor, old.card, before),
                partial(card_anchor, card, after),
            )
            chart, prices = load_chart(old.card), "none"
            if chart is None and old.card.get("pricing_artifact"):
                raise CommandError(f"{name}: the pinned price artifact is missing.")
            if chart is not None:
                moved = replaced(chart, old.index_id, index.id)
                published = price_quotes(chart)
                if published is None:
                    prices = "no validated price; carried as it is"
                else:
                    before, after = priced_bundle(old.index), priced_bundle(index)
                    plan = index.plan_key
                    same_anchors(
                        name,
                        published,
                        partial(quote_anchor, plan, before),
                        partial(quote_anchor, plan, after),
                    )
                    price_anchor(moved, after, plan, published[0])
                    prices = f"{len(published)} quotations open"
                path = report / "premiums" / (index.id + ".json")
                if path.exists() and json.loads(path.read_text()) != moved:
                    raise CommandError(
                        f"{name}: a different chart is already filed for {index.id}."
                    )
                atomic_json(path, moved)
                card.update(freeze_prices(index.id, target))
            identity = digest({"card": card, "source_version": old.id, "manifest": manifest})
            card["card_version"] = identity
            audit = replaced(json.loads(Path(old.audit_path).read_text()), old.index_id, index.id)
            path = target / "cards" / (identity + ".json")
            atomic_json(
                path,
                {
                    **audit,
                    "card": card,
                    "source_card_version": old.id,
                    "carried_from": {
                        "card_version": old.id,
                        "index_version": old.index_id,
                        "run_id": options["source_run"],
                    },
                },
            )
            DemoFactCard.objects.get_or_create(
                id=identity, defaults={"index": index, "card": card, "audit_path": str(path)}
            )
            completed.append({**item, "id": identity, "index": index.id})
            report_rows.append(
                {"plan": name, "card": identity, "quotations": len(quotes), "prices": prices}
            )
        atomic_json(target / "progress.json", {"completed": completed, "failures": []})
        if (source / "priority.json").exists():
            priority = {
                manifest["carried"].get(r["index"], r["index"])
                for r in json.loads((source / "priority.json").read_text())["cards"]
            }
            atomic_json(
                target / "priority.json",
                {"cards": [r for r in completed if r["index"] in priority], "failures": []},
            )
        atomic_json(target / "complete.json", {"cards": completed, "manifest": manifest})
        self.stdout.write(json.dumps({"cards": len(completed), "carried": report_rows}))
