"""The engine's answers to the canonical topic questions, computed ahead and shared.

The engine never reads the customer profile, so one validated answer per plan index,
topic and retrieval method serves every conversation. Only policy wording and the
canonical question are kept here; customer text never is."""

import copy
import re
import uuid
from collections import OrderedDict
from threading import Lock

from django.db import IntegrityError, transaction
from django.db.models import Q

from ..models import DemoPlanIndex, DemoTopicAnswer
from .answer_retrieval import EXPANSION_VERSION
from .answer_scope import SCOPE_VERSION, canon, exclusion, named, plain, question_topic, scope_for
from .answer_scope import TOPICS as SCOPE_TOPICS
from .answers import DRAFT_VERSION
from .bakeoff import QUESTIONS
from .services import bundle_for, decrypted, encrypted
from .table_cells import fields
from .validation import VALIDATOR_VERSION

TOPIC_QUESTIONS = {key: text for key, text, _ in QUESTIONS}
QUESTION_TOPICS = {text: key for key, text in TOPIC_QUESTIONS.items()}
TOPICS = tuple(TOPIC_QUESTIONS)
# How the customer would name each topic.
TOPIC_LABELS = {
    "room_rent": "room rent",
    "icu": "ICU charges",
    "ped": "the pre-existing disease waiting period",
    "specified_waiting": "the specified-disease waiting period",
    "maternity": "maternity cover",
    "newborn": "newborn cover",
    "copay": "co-pay",
    "deductible": "the deductible",
    "restoration": "restoration of cover",
    "no_claim_bonus": "the no-claim bonus",
    "pre_post": "pre- and post-hospitalisation cover",
    "day_care": "day-care treatment",
    "road_ambulance": "road ambulance cover",
    "air_ambulance": "air ambulance cover",
    "ayush": "AYUSH treatment",
    "organ_donor": "organ donor expenses",
    "home_care": "treatment at home (domiciliary)",
    "health_check": "health check-ups",
    "opd": "outpatient (OPD) cover",
    "cataract": "cataract treatment",
}
# Terms each plan states rather than benefits it adds; a waiting period is printed
# under an exclusion heading (Excl01), so exclusion wording never marks it excluded.
TERMS = {"room_rent", "ped", "specified_waiting", "copay", "deductible", "cataract"}
# Everyday words and misspellings the source topic patterns miss. Used only when the
# interpreting model is unavailable or disagrees with the customer's own words.
SYNONYMS = {
    "air_ambulance": r"\bheli\w*|\bair[ -]?lift|\bair[ -]?ambul\w*|\b(?:aero|air)plane\b|\bair transport",
    "road_ambulance": r"\bambul\w*",
    "health_check": r"check[ -]?ups?\b|health[ -]?check|preventive|annual (?:health )?check",
    "opd": r"\bopd\b|out[ -]?patient|doctor(?:'s)? (?:visits?|consultations?|fees?)|consultations?",
    "ped": r"pre[ -]?existing|\bped\b|diabet\w*|blood pressure|\bbp\b|hypertension|thyroid|asthma|"
    r"existing (?:illness|disease|condition)",
    "maternity": r"maternity|pregnan\w*|deliver(?:y|ies)|child ?birth|c-?section|caesarean",
    "newborn": r"new[ -]?born|baby",
    "room_rent": r"room",
    "icu": r"\bicu\b|intensive care",
    "home_care": r"domiciliary|home[ -]?(?:health[ -]?)?care|(?:treatment|hospitali[sz]ation) at home",
    "ayush": r"ayush|ayurved\w*|homeopath\w*|unani|siddha",
    "cataract": r"cataract",
    "organ_donor": r"organ donor|donor|transplant",
}
_ALIASES = {"room": "room_rent", "bonus": "no_claim_bonus"}
# "Not available" is left out: benefit tables print it against the smaller sums insured.
EXCLUDES = re.compile(
    r"\bexcluded\b|\bexclusions?\b|not (?:be )?(?:covered|payable|admissible)|"
    r"\bno (?:cover|coverage)\b|does not (?:cover|pay)|(?:shall|will) not pay",
    re.I,
)
# Standard exclusions are printed with an IRDAI code (Excl18 maternity, Excl01 PED).
EXCLUSION_CODE = re.compile(r"\bExcl\s*[-–]?\s*\d{1,2}\b|\bCode\s*[-–:]?\s*Excl", re.I)
# Clause numbering before a statement's first words ("8.", "B21.", "3.2.14", "A.").
NUMBERING = re.compile(r"^(?:[(\[]?(?:[A-Z]{0,2}\d+(?:\.\d+)*|[A-Za-z]|[ivxlc]+)[.)\]:]?\s+)+")
GROUPS = ("base", "addon", "excluded", "not_found")
# One benefit table printed for several variants: "C. Air Ambulance • Classic & Select
# Variant: NA • Elite & Black Variant: Up to INR 5L".
VARIANT_LINE = re.compile(r"([A-Za-z][\w+&,/ -]*?)\s+Variants?\s*[:–-]\s*(.+?)(?=\s*•|$)")
NEXT_ENTRY = re.compile(r"\s(?:[A-Z]|\d{1,2})\.\s+[A-Z]")
# A topic's own entry in such a table; "Air Ambulance" is never the road ambulance's.
ENTRIES = {"road_ambulance": r"(?<!air )(?<!air-)\bambul\w*"}
NOT_AVAILABLE = re.compile(r"(?:NA|N\.A\.?|N/A|Not (?:available|applicable|covered)|Nil)\b", re.I)
# A variant table's cell saying the variant hasn't the benefit: "NA" under MAX.
NOT_OFFERED = re.compile(r"NA|N\.A|N/A|Not (?:available|applicable|covered|offered)|[-–—]", re.I)


def topics_in(text):
    """Bank topics the customer's words name, from source patterns and synonyms."""
    found = [_ALIASES.get(t, t) for t in question_topic(text)]
    found += [t for t, pattern in SYNONYMS.items() if re.search(pattern, text, re.I)]
    if "air_ambulance" in found:
        found = [t for t in found if t != "road_ambulance"]
    return [t for t in dict.fromkeys(found) if t in TOPIC_QUESTIONS]


def topic_for(text, proposed=None):
    """The one bank topic a question is about, or None when it is free-form.

    The interpreting model's topic is kept unless the customer's own words name a
    different single topic; two or more named topics are a free-form question."""
    named = topics_in(text)
    if proposed in TOPIC_QUESTIONS and (not named or proposed in named):
        return proposed
    return named[0] if len(named) == 1 else None


def current(result):
    """A final answer from the engine versions in use now."""
    return bool(result) and (
        result.get("status") in {"answered", "not_found"}
        and result.get("validator") == VALIDATOR_VERSION
        and result.get("draft_contract") == DRAFT_VERSION
        and result.get("scope_contract") == SCOPE_VERSION
        and result.get("retrieval_contract") == EXPANSION_VERSION
    )


def remember(index, topic, method, result):
    """Keep a current, final engine answer for reuse; anything else is retried later.

    A validated answer is never replaced by a later not-found at the same versions."""
    if topic not in TOPIC_QUESTIONS or not current(result):
        return False
    row = DemoTopicAnswer.objects.filter(index=index, topic=topic, method=method).first()
    if row and row.status == "answered" and result["status"] != "answered":
        if (row.validator, row.draft) == (VALIDATOR_VERSION, DRAFT_VERSION):
            return False
    row = row or DemoTopicAnswer(id=uuid.uuid4(), index=index, topic=topic, method=method)
    row.status = result["status"]
    row.validator = result["validator"]
    row.draft = result["draft_contract"]
    row.result_ciphertext = encrypted(result, row.id)
    row.model = (result.get("models") or [""])[-1][:80]
    row.total_ms = result.get("total_ms", 0)
    try:
        with transaction.atomic():
            row.save()
    except IntegrityError:
        return False
    return True


def lookup(indexes, topic, method, *, siblings=()):
    """Current bank answers for these plan indexes, by index ID. With siblings (the IDs
    of the release's plan indexes), a plan whose own answer found nothing takes the
    wording its sibling variants' answers in that release quote for it (see `shared`)."""
    found = {}
    rows = DemoTopicAnswer.objects.filter(
        index__in=[i for i in indexes if not i.revoked_at],
        topic=topic,
        method=method,
        validator=VALIDATOR_VERSION,
        draft=DRAFT_VERSION,
    )
    for row in rows:
        result = decrypted(row.result_ciphertext, row.id)
        if current(result):
            found[row.index_id] = result
    if siblings:
        wanted = [
            (i, topic)
            for i in indexes
            if not i.revoked_at
            and (i.id not in found or group(found[i.id], topic, i.variant) == "not_found")
        ]
        found.update(
            {index_id: r for (index_id, _), r in borrowed(wanted, method, siblings).items()}
        )
    return found


# Each stored answer's group, keyed by row and its last update; rows change only by update.
_GROUPS = {}


def bank_groups(index_ids, method):
    """Where each plan's validated wording puts each topic, by index ID then topic. The
    IDs are one release's plan indexes; a variant borrows only from its siblings there."""
    index_ids = list(index_ids)
    rows = DemoTopicAnswer.objects.filter(
        index_id__in=index_ids,
        index__revoked_at__isnull=True,
        method=method,
        validator=VALIDATOR_VERSION,
        draft=DRAFT_VERSION,
    )
    keys = list(rows.values_list("id", "index_id", "topic", "updated_at"))
    missing = [row_id for row_id, _, _, updated in keys if (row_id, updated) not in _GROUPS]
    for row in DemoTopicAnswer.objects.filter(pk__in=missing).select_related("index"):
        result = decrypted(row.result_ciphertext, row.id)
        _GROUPS[(row.id, row.updated_at)] = (
            group(result, row.topic, row.index.variant) if current(result) else None
        )
    found = {}
    for row_id, index_id, topic, updated in keys:
        if _GROUPS.get((row_id, updated)):
            found.setdefault(index_id, {})[topic] = _GROUPS[(row_id, updated)]
    # A variant whose own answer found nothing reads what its siblings' answers quote.
    plans = DemoPlanIndex.objects.filter(pk__in=index_ids, revoked_at__isnull=True)
    variants = {i.id: i.variant for i in plans}
    wanted = [
        (i, t)
        for i in plans
        for t in TOPICS
        if found.get(i.id, {}).get(t, "not_found") == "not_found"
    ]
    for (index_id, topic), result in borrowed(wanted, method, index_ids).items():
        found.setdefault(index_id, {})[topic] = group(result, topic, variants[index_id])
    return found


def statements(result):
    return ((result or {}).get("answer") or {}).get("statements", [])


def opening(text):
    """A statement's heading and first sentence, which say whether it grants or excludes."""
    flat = " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", text).split())
    flat = NUMBERING.sub("", flat)
    return re.split(r"(?<=[a-z)][.;])\s", flat, maxsplit=1)[0][:300]


def wording(statement):
    parts = [statement.get("heading", ""), statement.get("text", "")]
    parts += [c.get("text", "") for c in statement.get("conditions", [])]
    return " ".join(" ".join(parts).split())


# Where a clause starts inside a long quote: after a full stop, semicolon, colon or
# bullet, at clause numbering ("4.30.", "B26.", "c)"), or after a parenthetical phrase
# that closes a table row ("(as per list I, II) Wellconsult+"; never a mark like "(6)").
CLAUSE = re.compile(
    r"(?:[.;:]|•)\s+|\s(?=(?:[A-Z]{0,2}\d+(?:\.\d+)*|[a-z])[.)]\s)|\([^()]*[\s,][^()]*\)\s+(?=[A-Z])"
)


def topic_patterns(topic):
    scope = {v: k for k, v in _ALIASES.items()}.get(topic, topic)
    return [p for p in (SYNONYMS.get(topic), SCOPE_TOPICS.get(scope)) if p]


def card_quotes(found, topic):
    """Fact-card statements as shown in a topic table: each excerpt cut to its clause on
    the topic, excerpts that never name it left out when another does, repeats dropped."""
    patterns = topic_patterns(topic)
    shown = [focused(statement, topic) for statement in found]
    named = {
        e for x in shown for e in x["excerpts"] if any(re.search(p, e, re.I) for p in patterns)
    }
    kept, seen = [], set()
    for statement in shown:
        excerpts = []
        for e in statement["excerpts"]:
            key = " ".join(e.removeprefix("… ").split()[:20])
            if (e in named or not named) and key not in seen:
                seen.add(key)
                excerpts.append(e)
        if excerpts:
            kept.append({**statement, "excerpts": excerpts})
    return kept


def focused(statement, topic, size=360):
    """A long fact-card quote cut to the clause that names the topic, for display. The
    words stay verbatim, a cut is marked "…", and the citations still open the whole
    quote."""
    patterns = topic_patterns(topic)
    shown = []
    for text in statement.get("excerpts") or [statement.get("text", "")]:
        flat = " ".join(text.split())
        hits = [m.start() for p in patterns if (m := re.search(p, flat, re.I))]
        if len(flat) <= size or not hits:
            shown.append(flat)
            continue
        at = min(hits)
        cuts = [m.end() for m in CLAUSE.finditer(flat, max(0, at - size // 2), at)]
        start = cuts[-1] if cuts else flat.rfind(" ", 0, max(0, at - 40)) + 1
        end = start + size
        if end < len(flat):
            stops = [m.end() for m in re.finditer(r"[.;]\s", flat[start + size // 2 : end])]
            end = start + size // 2 + stops[-1] if stops else flat.rfind(" ", start, end)
        part = flat[start:end].strip()
        shown.append(("… " if start else "") + part + (" …" if end < len(flat) else ""))
    return {**statement, "excerpts": list(dict.fromkeys(shown))}


def relevant(statement, topic):
    """Whether the quote itself names the topic; validated quotes can drift to a neighbour."""
    return topic in topics_in(wording(statement))


def negative(text):
    return bool(EXCLUDES.search(text))


def excludes(statement, topic=None):
    """A statement that withholds cover: a coded standard exclusion, an exclusion opening,
    or a first sentence about the topic that withholds it or is headed by an exclusion
    code ("Maternity Expenses (Code-Excl18)" further down an exclusion list)."""
    text = " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", statement.get("text", "")).split())
    # A benefit clause may cite a code further on; the code must lead the statement.
    if EXCLUSION_CODE.search(text[:200]) or negative(opening(text)):
        return True
    if topic:
        for sentence in re.split(r"(?<=[.;])\s+(?=[A-Z])", text):
            if topic in topics_in(sentence):
                return negative(sentence) or bool(EXCLUSION_CODE.search(sentence[:80]))
    return False


def variant_says(text, topic, variant):
    """What a table printed for several variants gives this variant under the topic's
    entry, or None when the wording isn't split by variant."""
    pattern = ENTRIES.get(topic, SYNONYMS.get(topic))
    flat = " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", text).split())
    found = re.search(pattern, flat, re.I) if pattern and variant else None
    if not found:
        return None
    rest = flat[found.end() :]
    end = NEXT_ENTRY.search(rest)
    for names, value in VARIANT_LINE.findall(rest[: end.start()] if end else rest):
        listed = {n.strip().casefold() for n in re.split(r"&|,|/|\band\b", names)}
        if variant.casefold() in listed:
            return value.strip()
    return None


def withheld(statement, topic, variant=None):
    """A statement that withholds the topic from this plan: its variant's own entry says
    it isn't available, or the wording excludes it."""
    value = variant_says(statement.get("text", ""), topic, variant)
    if value is not None:
        return bool(NOT_AVAILABLE.match(value))
    return excludes(statement, topic)


def not_offered(statement, topic=None):
    """A table statement whose value cell says the variant hasn't the benefit. It is
    never evidence of cover; in an optional-covers table it often means the cover is
    already in-built, so there it decides nothing. A cell that labels several fields
    ("Road Ambulance: INR 2000\nAir Ambulance: NA") says it under the topic's label."""
    excerpts = statement.get("excerpts") or []
    if not statement.get("table") or not excerpts:
        return False
    # A table statement quotes its row labels, column labels and value, in that order.
    printed = fields(excerpts[-1]) if topic else {}
    patterns = topic_patterns(topic) if printed else []
    own = [v for k, v in printed.items() if any(re.search(p, k, re.I) for p in patterns)]
    values = own or [" ".join(excerpts[-1].split())]
    return all(NOT_OFFERED.fullmatch(v.strip(" .")) for v in values)


def group(result, topic, variant=None):
    """Where the plan's validated wording puts this topic: base, addon, excluded or not_found."""
    if not result or result.get("status") != "answered":
        return "not_found"
    found = statements(result)
    # Statements that name the topic decide; when none does, the validated set stands.
    found = [s for s in found if relevant(s, topic)] or found
    base = [s for s in found if s.get("coverage_scope", "base") == "base"]
    optional = [
        s for s in found if s.get("coverage_scope", "base") != "base" and not not_offered(s, topic)
    ]
    if any(
        not not_offered(s, topic) and (topic in TERMS or not withheld(s, topic, variant))
        for s in base
    ):
        return "base"
    if optional:
        return "addon"
    if base:
        return "base" if topic in TERMS else "excluded"
    return "not_found"


def mentions(result, words):
    """Whether the validated wording itself uses one of the customer's words."""
    text = " ".join(
        part.get("text", "")
        for s in statements(result)
        for part in [s, *s.get("conditions", []), *s.get("restrictions", [])]
    )
    return any(re.search(r"\b" + re.escape(w) + r"\w*", text, re.I) for w in words)


# Variants of one product printed in the same documents, such as ReAssure 3.0 Classic,
# Select, Elite and Black. The engine reads each variant on its own and can miss wording
# a sibling found; the shared documents decide whether that wording is this variant's
# too. Outcomes are kept by plan index and the sibling row's last update.
_SHARED = {}
_BUNDLES = OrderedDict()
_BUNDLES_LOCK = Lock()


def index_bundle(index):
    """A plan index's bundle; it is content-addressed, so it never changes under its ID."""
    with _BUNDLES_LOCK:
        if index.id in _BUNDLES:
            _BUNDLES.move_to_end(index.id)
            return _BUNDLES[index.id]
    bundle = bundle_for(index)
    with _BUNDLES_LOCK:
        _BUNDLES[index.id] = bundle
        while len(_BUNDLES) > 8:
            _BUNDLES.popitem(last=False)
    return bundle


def borrowed(wanted, method, among):
    """What sibling variants' validated answers give each (plan index, topic) pair, by
    (index ID, topic); pairs no sibling's wording covers are left out. Siblings come
    only from these plan index IDs (one release's), never another edition's index."""
    products = {(i.insurer, i.name, i.uin) for i, _ in wanted}
    if not products:
        return {}
    either = Q()
    for insurer, name, uin in products:
        either |= Q(insurer=insurer, name=name, uin=uin)
    family = {
        i.id: i
        for i in DemoPlanIndex.objects.filter(either, pk__in=list(among), revoked_at__isnull=True)
    }
    rows = DemoTopicAnswer.objects.filter(
        index_id__in=list(family),
        topic__in={t for _, t in wanted},
        method=method,
        validator=VALIDATOR_VERSION,
        draft=DRAFT_VERSION,
        status="answered",
    ).order_by("index__variant", "index_id")
    answered = {}
    for row_id, index_id, topic, updated in rows.values_list(
        "id", "index_id", "topic", "updated_at"
    ):
        answered.setdefault(topic, []).append((row_id, family[index_id], updated))
    found = {}
    for index, topic in wanted:
        for row_id, sibling, updated in answered.get(topic, []):
            if sibling.variant == index.variant or (sibling.insurer, sibling.name, sibling.uin) != (
                index.insurer,
                index.name,
                index.uin,
            ):
                continue
            key = (index.id, row_id, updated)
            if key not in _SHARED:
                row = DemoTopicAnswer.objects.get(pk=row_id)
                result = decrypted(row.result_ciphertext, row.id)
                _SHARED[key] = shared(result, topic, index, sibling) if current(result) else None
            if _SHARED[key]:
                found[(index.id, topic)] = copy.deepcopy(_SHARED[key])
                break
    return found


def shared(result, topic, index, sibling):
    """A sibling variant's validated answer, kept to the statements their shared documents
    give this variant too and pointed at this plan's own sources; None when none does.

    A statement carries over when it prints this variant's own entry ("Classic & Select
    Variant: NA"), when it is one benefit-table cell printed across every variant's
    column, or when it names no variant in wording the engine's scope rules hold for
    every variant alike. Every quote kept must be printed at the same place in this
    plan's own documents."""
    try:
        origin, target = index_bundle(sibling), index_bundle(index)
    except (OSError, ValueError):
        return None
    kept = [
        (n, *found)
        for n, s in enumerate(statements(result))
        if (found := carried(s, topic, index.variant, origin))
    ]
    validation = result.get("validation") or {}
    anchors = validation.get("anchors") or []
    mapping = validation.get("statement_anchors")
    # Answers stored before per-statement mapping link every anchor to every statement.
    if not kept or (mapping is None and len(kept) < len(statements(result))):
        return None
    positions = {
        n: [p for p in (mapping[n] if mapping else range(len(anchors))) if p < len(anchors)]
        for n, _, _ in kept
    }
    for n, _, dropped in kept:
        positions[n] = [
            p for p in positions[n] if one_line(anchors[p].get("quote", "")) not in dropped
        ]
    used = sorted({p for found in positions.values() for p in found})
    sections = section_ids(origin, target)
    if not used or not all(
        opens(anchors[p], target) and anchors[p].get("section_id") in sections for p in used
    ):
        return None
    moved = {p: n for n, p in enumerate(used)}
    shown = []
    for _, statement, _ in kept:
        parts = {}
        for field in ("conditions", "restrictions"):
            if field in statement:
                parts[field] = [
                    {**c, "citations": cited(c.get("citations", []), sections)}
                    for c in statement[field]
                ]
        shown.append(
            {**statement, **parts, "citations": cited(statement.get("citations", []), sections)}
        )
    plan_id = target.get("policy_version_id") or result.get("plan_id")
    answer = {**result["answer"], "plan_id": plan_id, "statements": shown}
    return {
        **{k: v for k, v in result.items() if k not in {"packet", "attempts"}},
        "plan_id": plan_id,
        "index_version": index.id,
        "answer": answer,
        "validation": {
            **validation,
            "anchors": [
                {**anchors[p], "section_id": sections[anchors[p]["section_id"]]} for p in used
            ],
            "statement_anchors": [[moved[p] for p in positions[n]] for n, _, _ in kept]
            if mapping
            else None,
        },
        "shared_from": {"index": sibling.id, "variant": sibling.variant},
    }


def carried(statement, topic, variant, bundle):
    """A sibling's statement as this variant's own, with the quotes it no longer shows;
    None when the documents don't give it to this variant."""
    if variant_says(statement.get("text", ""), topic, variant) is not None:
        found = {**statement, "scope_variant": variant}, set()
    elif statement.get("table"):
        found = spanned(statement, variant, bundle)
    else:
        found = unscoped(statement, topic, variant, bundle)
    if not found:
        return None
    shown, dropped = found
    kept = supported(shown, topic, variant, bundle, strict=False)
    if kept is None:
        return None
    shown, gone = kept
    # A quote a kept part still cites stays linked. Anchors hold quotes trimmed.
    return shown, {one_line(q) for q in dropped | gone} - {
        one_line(c.get("quote", "")) for c in quotes(shown)
    }


def quotes(statement):
    parts = [statement, *statement.get("conditions", []), *statement.get("restrictions", [])]
    return [c for part in parts for c in part.get("citations", [])]


def supported(statement, topic, variant, bundle, *, strict):
    """The statement with the supporting clauses that hold for this variant, and the
    quotes of those left out. A clause naming only other variants is left out; with
    strict, a clause about the topic that names any variant decides it variant by
    variant, so the statement isn't carried (None)."""
    names = [canon(v) for v in bundle.get("variants", [])]
    shown, gone = {**statement}, set()
    for field in ("conditions", "restrictions"):
        if field not in statement:
            continue
        shown[field] = []
        for clause in statement[field]:
            text = one_line(clause.get("text", ""))
            listed = {n for n in names if named(text, n)}
            if listed and strict and topic in topics_in(text):
                return None
            if listed and len(listed) < len(names) and canon(variant) not in listed:
                gone |= {c.get("quote", "") for c in clause.get("citations", [])}
            else:
                shown[field].append(clause)
    return shown, gone


def one_line(text):
    return " ".join(text.split())


def spanned(statement, variant, bundle):
    """A benefit-table cell printed once across several variants' columns. The table
    reader files it under its first column and records the columns it spans, so the
    sibling's answer is this variant's entry too when the cell spans this variant's
    column under the header the sibling cites."""
    ref = statement["table"]
    table = next((t for t in bundle.get("tables", []) if t["id"] == ref.get("region_id")), None)
    cells = table["cells"] if table else {}
    value = cells.get(ref.get("value_cell_id"))
    heads = {cells[k]["row"] for k in ref.get("column_label_ids", []) if k in cells}
    own = [c for c in cells.values() if c["row"] in heads and canon(c["text"]) == canon(variant)]
    if not value or len(own) != 1 or own[0]["row"] >= value["row"]:
        return None
    if not value["column"] <= own[0]["column"] <= value.get("column_end", value["column"]):
        return None
    labels = {cells[k]["text"] for k in ref.get("column_label_ids", []) if k in cells}
    excerpts = [e for e in statement.get("excerpts", []) if e not in labels]
    shown = {
        **statement,
        "excerpts": excerpts,
        "citations": [c for c in statement.get("citations", []) if c.get("quote") not in labels],
        "table": {**ref, "column_label_ids": [own[0]["id"]]},
        "scope_variant": variant,
    }
    if statement.get("text") == "\n\n".join(statement.get("excerpts", [])):
        shown["text"] = "\n\n".join(excerpts)
    return shown, labels


def unscoped(statement, topic, variant, bundle):
    """Wording that names no variant, under no heading or clause that limits it to some
    variants, on a topic the variant tables don't split (unless it excludes it): the
    engine's scope rules give it to every variant alike. A supporting clause may print
    variants' entries for other benefits; those naming only other variants are left out."""
    names = bundle.get("variants", [])
    if not statement.get("citations") or any(named(statement.get("text", ""), v) for v in names):
        return None
    kept = supported(statement, topic, variant, bundle, strict=True)
    if kept is None:
        return None
    statement, gone = kept
    parts = [statement, *statement.get("conditions", []), *statement.get("restrictions", [])]
    try:
        scope = scope_for(bundle)
    except ValueError:
        return None
    key = {v: k for k, v in _ALIASES.items()}.get(topic, topic)
    split = {k for matrix in scope.matrices.values() for k in matrix["topics"]}
    if key in split and not exclusion(plain(statement.get("text", ""))):
        return None
    for part in parts:
        for c in part.get("citations", []):
            section = scope.sections.get(c.get("section_id"))
            segment = next(
                (s for s in (section.segments if section else ()) if s.page_id == c.get("page_id")),
                None,
            )
            if not segment:
                return None
            try:
                context = scope.context(section, segment, c["quote"], c.get("occurrence", 0))
            except ValueError:
                return None
            applies = {canon(n) for n in context["named_applicability"]}
            if applies and canon(variant) not in applies:
                return None
    return {**statement, "scope_variant": variant}, gone


def section_ids(origin, target):
    """Each section of a sibling's bundle mapped to the same printed section in this one."""

    def printed(section):
        pages = tuple((s["page_id"], s["start"], s["end"]) for s in section["segments"])
        return section["document_sha256"], tuple(section["title_path"]), pages

    ours = {printed(s): s["id"] for s in target.get("sections", [])}
    return {s["id"]: ours[printed(s)] for s in origin.get("sections", []) if printed(s) in ours}


def cited(citations, sections):
    return [
        {**c, "section_id": sections.get(c.get("section_id"), c.get("section_id"))}
        for c in citations
    ]


def opens(anchor, bundle):
    """Whether a quote is printed at the same place in this bundle's own documents."""
    sha = anchor.get("document_sha256")
    if sha not in {d["sha256"] for d in bundle.get("documents", [])}:
        return False
    page = next(
        (
            p
            for p in bundle.get("pages", [])
            if p["evidence_span_id"] == anchor.get("page_id") and p.get("document_sha256") == sha
        ),
        None,
    )
    start, end = anchor.get("start"), anchor.get("end")
    return bool(page) and start is not None and page["passage"][start:end] == anchor.get("quote")
