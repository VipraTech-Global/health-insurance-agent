"""The engine's answers to the canonical topic questions, computed ahead and shared.

The engine never reads the customer profile, so one validated answer per plan index,
topic and retrieval method serves every conversation. Only policy wording and the
canonical question are kept here; customer text never is."""

import re
import uuid

from django.db import IntegrityError, transaction

from ..models import DemoTopicAnswer
from .answer_retrieval import EXPANSION_VERSION
from .answer_scope import SCOPE_VERSION, question_topic
from .answer_scope import TOPICS as SCOPE_TOPICS
from .answers import DRAFT_VERSION
from .bakeoff import QUESTIONS
from .services import decrypted, encrypted
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
NOT_AVAILABLE = re.compile(r"(?:NA|N\.A\.?|N/A|Not (?:available|applicable|covered)|Nil)\b", re.I)


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


def lookup(indexes, topic, method):
    """Current bank answers for these plan indexes, by index ID."""
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
    return found


# Each stored answer's group, keyed by row and its last update; rows change only by update.
_GROUPS = {}


def bank_groups(index_ids, method):
    """Where each plan's validated wording puts each topic, by index ID then topic."""
    rows = DemoTopicAnswer.objects.filter(
        index_id__in=list(index_ids),
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
    or a first sentence about the topic that withholds it."""
    text = " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", statement.get("text", "")).split())
    # A benefit clause may cite a code further on; the code must lead the statement.
    if EXCLUSION_CODE.search(text[:200]) or negative(opening(text)):
        return True
    if topic:
        for sentence in re.split(r"(?<=[.;])\s+(?=[A-Z])", text):
            if topic in topics_in(sentence):
                return negative(sentence)
    return False


def variant_says(text, topic, variant):
    """What a table printed for several variants gives this variant under the topic's
    entry, or None when the wording isn't split by variant."""
    pattern = SYNONYMS.get(topic)
    flat = " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", text).split())
    found = re.search(pattern, flat, re.I) if pattern and variant else None
    if not found:
        return None
    rest = flat[found.end() :]
    end = NEXT_ENTRY.search(rest)
    for names, value in VARIANT_LINE.findall(rest[: end.start()] if end else rest):
        named = {n.strip().casefold() for n in re.split(r"&|,|/|\band\b", names)}
        if variant.casefold() in named:
            return value.strip()
    return None


def withheld(statement, topic, variant=None):
    """A statement that withholds the topic from this plan: its variant's own entry says
    it isn't available, or the wording excludes it."""
    value = variant_says(statement.get("text", ""), topic, variant)
    if value is not None:
        return bool(NOT_AVAILABLE.match(value))
    return excludes(statement, topic)


def group(result, topic, variant=None):
    """Where the plan's validated wording puts this topic: base, addon, excluded or not_found."""
    if not result or result.get("status") != "answered":
        return "not_found"
    found = statements(result)
    # Statements that name the topic decide; when none does, the validated set stands.
    found = [s for s in found if relevant(s, topic)] or found
    base = [s for s in found if s.get("coverage_scope", "base") == "base"]
    optional = [s for s in found if s.get("coverage_scope", "base") != "base"]
    if base and (topic in TERMS or any(not withheld(s, topic, variant) for s in base)):
        return "base"
    if optional:
        return "addon"
    return "excluded" if base else "not_found"


def mentions(result, words):
    """Whether the validated wording itself uses one of the customer's words."""
    text = " ".join(
        part.get("text", "")
        for s in statements(result)
        for part in [s, *s.get("conditions", []), *s.get("restrictions", [])]
    )
    return any(re.search(r"\b" + re.escape(w) + r"\w*", text, re.I) for w in words)
