"""Source-only product, variant and optional-cover gates for displayed answers."""

import re
from bisect import bisect_right
from collections import OrderedDict
from threading import RLock

from .assembly import EvidenceInsufficient, PacketLabels, document_source
from .evidence import Section
from .quotations import locate

SCOPE_VERSION = "original-scope/1"
OPTIONAL = re.compile(
    r"\boptional\b|\badd[ -]?ons?\b|\briders?\b|\bextra premium\b|\badditional premium\b",
    re.I,
)
TOPICS = {
    "icu": r"\bICU\b|intensive care",
    "day_care": r"day[ -]?care",
    "road_ambulance": r"road ambulance",
    "pre_post": r"pre[ -]?(?:and post[ -]?)?hospitali[sz]ation|post[ -]?hospitali[sz]ation",
    "organ_donor": r"organ donor|donor expenses",
    "home_care": r"domiciliary|home[ -]?care",
    "ped": r"pre[ -]?existing|\bPED\b|Excl\s*0?1\b",
    "specified_waiting": r"specified (?:disease|illness)|specific (?:disease|illness)|Excl\s*0?2\b",
    "deductible": r"deductible",
    "copay": r"co[ -]?pay(?:ment)?",
    "room": r"room|boarding",
    "maternity": r"maternity|delivery|deliveries|childbirth",
    "newborn": r"new[ -]?born",
    "opd": r"out[ -]?patient|\bOPD\b",
    "restoration": r"restor|recharg|reload|reinstate",
    "bonus": r"bonus|no[ -]?claim",
    "ayush": r"AYUSH|Ayurveda|Unani|Siddha|Homeopath",
    "air_ambulance": r"air ambulance",
    "health_check": r"health[ -]?check|check[ -]?up",
    "cataract": r"cataract",
    "sum_insured": r"sum insured (?:options|choices)|base sum insured",
}


class ScopeViolation(EvidenceInsufficient):
    pass


def canon(value):
    return " ".join(value.split()).casefold()


def named(text, name):
    return bool(re.search(r"(?<!\w)" + re.escape(canon(name)) + r"(?![\w+])", canon(text)))


def question_topic(question):
    # Prefer specific topics over broader mentions in a compound customer query.
    return [key for key, pattern in TOPICS.items() if re.search(pattern, question, re.I)]


def exclusion(text):
    return bool(
        re.search(
            r"not (?:covered|payable|available)|exclusions?|shall not pay|will not pay", text, re.I
        )
    )


def optional_cover(text):
    """A base exclusion may mention an optional exception, but a separate positive
    optional sentence cannot inherit that exclusion's classification."""
    for match in OPTIONAL.finditer(text):
        left = max(text.rfind(".", 0, match.start()), text.rfind(";", 0, match.start())) + 1
        ends = [n for n in (text.find(".", match.end()), text.find(";", match.end())) if n >= 0]
        clause = text[left : min(ends) if ends else len(text)]
        if not exclusion(clause):
            return True
    return False


def is_optional_heading(match):
    title = match["title"].strip(" \t\x07➢•")
    if not OPTIONAL.search(title) or len(title.split()) > 14:
        return False
    # Sentences, FAQs, table-column headings and payment conditions are not
    # parent section headings. Numbered optional/rider titles may wrap.
    if re.search(r"\b(?:will|shall|payment|premium|insured|if|claim|not|exclusion)\b", title, re.I):
        return False
    if match["number"]:
        return bool(re.search(r"^(?:optional|riders?\b)|\brider(?:[ :(-]|$)", title, re.I))
    return bool(
        re.fullmatch(r"(?:Optional (?:Covers?|Benefits)|Riders?|Add[ -]?on Covers?)", title, re.I)
    )


class ScopeIndex:
    def __init__(self, bundle):
        self.product = bundle.get("name", "Selected plan")
        self.variant = bundle.get("variant", "Default")
        self.sections = {s["id"]: Section.from_payload(s) for s in bundle["sections"]}
        self.documents = {}
        self.headings = {}
        for section in self.sections.values():
            key = (section.document_id, section.document_sha256)
            if key not in self.documents:
                raw = document_source(section, list(self.sections.values()))
                self.documents[key] = raw
                self.headings[key] = list(
                    re.finditer(
                        r"(?m)^[ \t]*(?:(?P<number>(?:[A-Z]\.)?\d+(?:\.\d+)*|[A-Z])(?=[.)\s])[.)]?[ \t\x07]*)?(?P<title>[^\n]{2,150})$",
                        raw,
                    )
                )
        self.names = {v for v in bundle.get("variants", []) if v != "Default"}
        self.aliases = {canon(self.product), canon(self.variant)} - {"default", "selected plan"}
        self.product_names = {
            m[1].strip()
            for raw in self.documents.values()
            for m in re.finditer(
                r"(?mi)^(?:Product Name|Name of (?:the )?Product|Plan Name)\s*:\s*([^\n]{3,90})$",
                raw,
            )
        }
        self.names.update(self.product_names)
        self.matrices = {}
        for table in bundle.get("tables", []):
            cells = list(table["cells"].values())
            headers = [c for c in cells if c["row"] <= 2 and len(c["text"].split()) <= 5]
            if any(
                named(c["text"], v) or canon(v) in canon(c["text"])
                for c in headers
                for v in self.names
            ):
                candidates = {
                    " ".join(c["text"].split())
                    for c in headers
                    if c["column"] > 0
                    and c["row"] == 0
                    and not re.search(
                        r"\d|%|insured|waiting|period|benefit|section|plan[s]?\b|coverage|limit",
                        c["text"],
                        re.I,
                    )
                    and len(c["text"].strip()) > 1
                }
                self.names.update(candidates)
        for table in bundle.get("tables", []):
            headers = [c for c in table["cells"].values() if c["row"] <= 2]
            entities = {v for v in self.names if any(canon(c["text"]) == canon(v) for c in headers)}
            if len(entities) > 1 or (entities and len(bundle.get("variants", [])) > 1):
                self.matrices[table["id"]] = {
                    "names": sorted(entities),
                    "topics": [
                        k
                        for k, pat in TOPICS.items()
                        if any(re.search(pat, c["text"], re.I) for c in table["cells"].values())
                    ],
                }
        self.heading_starts = {k: [m.start() for m in v] for k, v in self.headings.items()}
        self.optional_headings = {
            k: [m for m in v if is_optional_heading(m)] for k, v in self.headings.items()
        }
        self.table_map = {t["id"]: t for t in bundle.get("tables", [])}
        self.roles = {s.document_id: s.role for s in self.sections.values()}
        self.document_labels = {
            str(d["document_version_id"]): d.get("label", "") for d in bundle.get("documents", [])
        }

    def context(self, section, segment, quote, occurrence=0):
        a, b = locate(segment.text, quote, occurrence)
        start = segment.document_start + a
        key = (section.document_id, section.document_sha256)
        raw = self.documents[key]
        before = raw[max(0, start - 12000) : start]
        # An enclosing numbered optional section continues through its children,
        # and ends at the next sibling or higher-level numbered heading.
        optional = section.role in {"rider", "add_on", "addon", "optional_cover"}
        scope_quotes = []
        headings = self.headings[key]
        stops = self.heading_starts[key]
        prior = headings[: bisect_right(stops, start)]
        for heading in reversed(self.optional_headings[key]):
            if heading.start() > start:
                continue
            title = heading["title"].strip()
            if re.search(r"(?:except|unless|excluding|not covered|not available)", title, re.I):
                continue
            number = heading["number"]
            if not number:
                later = raw[heading.end() : start]
                if re.search(
                    r"(?mi)^\s*(?:(?:Base|Standard|General) (?:Covers|Benefits|Exclusions|Conditions)|Sub ?Limits|Waiting Periods?|Exclusions)\b",
                    later,
                ):
                    continue
            else:
                if any(
                    m["number"]
                    and closes_scope(number, m["number"])
                    and m.start() > heading.start()
                    for m in prior
                ):
                    continue
            optional = True
            scope_quotes.append(heading[0])
            break
        local = segment.text[a:b]
        # Merely mentioning an optional exception in a base exclusion does not
        # convert the exclusion to an optional benefit.
        if optional_cover(local):
            optional = True
        applicable = re.findall(
            r"(?:applicable|available|covered|only)\s+(?:under|for|in|to)\s+([^.;\n]{1,100})",
            before[-800:] + local,
            re.I,
        )
        names = {v for v in self.names if any(named(t, v) for t in applicable)}
        owners = [m for m in prior if any(canon(m["title"]) == canon(v) for v in self.names)]
        if owners:
            owner = owners[-1]
            if not owner["number"] or not any(
                m["number"] and closes_scope(owner["number"], m["number"])
                for m in prior
                if m.start() > owner.start()
            ):
                names = {v for v in self.names if canon(owner["title"]) == canon(v)}
        product_owners = [
            m
            for m in prior
            if re.match(
                r"(?:Product Name|Name of (?:the )?Product|Plan Name)\s*:", m["title"], re.I
            )
        ]
        product_owner = (
            product_owners[-1]["title"].split(":", 1)[1].strip() if product_owners else None
        )
        return {
            "coverage_scope": "optional, extra premium" if optional else "base",
            "named_applicability": sorted(names),
            "printed_product_owner": product_owner,
            "scope_headings": scope_quotes,
        }

    def table_scope(self, table):
        cells = table["cells"]
        optional_rows = [
            c["row"]
            for c in cells.values()
            if re.fullmatch(r"Optional (?:Benefits|Covers)", c["text"].strip(), re.I)
        ]
        return {
            "selected_variant": self.variant,
            "variant_headers": {
                k: c["text"]
                for k, c in cells.items()
                if any(canon(c["text"]) == canon(v) for v in self.names)
            },
            "optional_rows_after": optional_rows,
        }

    def check(self, unit, labels, statement, question):
        main = []
        contexts = []
        for ref in [*unit.benefit, *unit.conditions, *unit.restrictions]:
            if ref.passage not in labels.passages:
                continue  # Assembly rejects unknown labels before this gate.
            section, segment = labels.passages[ref.passage]
            if ref in unit.benefit:
                main.append(ref.quote)
            contexts.append(self.context(section, segment, ref.quote, ref.occurrence))
        raw = " ".join(main)
        if (
            re.search(r"\bmeans\b|\brefers to\b", raw, re.I)
            and not re.search(
                r"\b(?:we|company|policy|insurer)\b.{0,100}\b(?:cover|pay|indemnif)|\bcovered\b|\bnot covered\b",
                raw,
                re.I | re.S,
            )
            and not re.search(r"meaning|define|definition|what does .* mean", question, re.I)
            and not unit.table
        ):
            raise ScopeViolation(
                "A definition alone does not establish this plan's cover or limit."
            )
        if (
            not statement.table
            and len(statement.text.split()) <= 7
            and not re.search(
                r"\d|covered|excluded|payable|available|unlimited|no limit", statement.text, re.I
            )
        ):
            raise ScopeViolation("A heading alone does not establish substantive cover.")
        topics = question_topic(question)
        if topics and not any(re.search(TOPICS[k], raw, re.I) for k in topics) and not unit.table:
            raise ScopeViolation(
                "Selected benefit quotation does not identify the requested field; include its governing heading."
            )
        if (
            "ped" in topics
            and "specified_waiting" not in topics
            and re.search(TOPICS["specified_waiting"], raw, re.I)
            and not re.search(TOPICS["ped"], raw, re.I)
        ):
            raise ScopeViolation("Specified-disease waiting is not pre-existing-disease waiting.")
        if (
            "deductible" in topics
            and not re.search(TOPICS["deductible"], raw, re.I)
            and not unit.table
        ):
            raise ScopeViolation("Co-payment or another limit is not a deductible answer.")
        required_optional = any(c["coverage_scope"] != "base" for c in contexts)
        for context in contexts:
            owner = context.get("printed_product_owner")
            selected_tokens = set(re.findall(r"[a-z0-9]+", canon(self.product))) - {"my"}
            selected_tokens = (
                selected_tokens - set(re.findall(r"[a-z0-9]+", canon(self.variant)))
            ) or selected_tokens
            owner_tokens = set(re.findall(r"[a-z0-9]+", canon(owner or "")))
            if (
                owner
                and canon(owner) not in self.aliases
                and selected_tokens
                and not selected_tokens <= owner_tokens
            ):
                raise ScopeViolation(
                    "Original product heading belongs to another product: " + owner
                )
            names = context["named_applicability"]
            if names and not unit.table and not any(canon(v) in self.aliases for v in names):
                raise ScopeViolation(
                    "The governing applicability clause names another variant/product: "
                    + ", ".join(names)
                )
        table_proven = False
        if statement.table:
            table = self.table_map.get(statement.table.region_id)
            if table:
                support = statement.table
                axes = [
                    table["cells"][k]
                    for k in [*support.row_label_ids, *support.column_label_ids]
                    if k in table["cells"]
                ]
                value = table["cells"].get(support.value_cell_id)
                matrix = self.matrices.get(table["id"])
                axis_text = " ".join(c["text"] for c in axes)
                if topics and not any(re.search(TOPICS[k], axis_text, re.I) for k in topics):
                    raise ScopeViolation(
                        "Table axes do not identify the requested benefit or field."
                    )
                if matrix and not any(canon(c["text"]) in self.aliases for c in axes):
                    raise ScopeViolation(
                        "Shared table requires the selected variant/product axis, not another plan column."
                    )
                table_proven = bool(matrix)
                if value and any(
                    value["row"] > r for r in self.table_scope(table)["optional_rows_after"]
                ):
                    required_optional = True
        shared_topics = {k for t in self.matrices.values() for k in t["topics"]}
        if any(k in shared_topics for k in topics) and not table_proven and not exclusion(raw):
            named_selected = bool(
                re.search(
                    r"(?:applicable|available|covered)\s+(?:under|for|to)\s+"
                    + re.escape(self.variant)
                    + r"\b",
                    raw,
                    re.I,
                )
            )
            cis = all(
                labels.passages[r.passage][0].role == "customer_information_sheet"
                and named(
                    self.document_labels.get(labels.passages[r.passage][0].document_id, ""),
                    self.variant,
                )
                and not re.search(
                    r"illustration|example",
                    self.document_labels.get(labels.passages[r.passage][0].document_id, ""),
                    re.I,
                )
                for r in unit.benefit
            )
            if not named_selected and not cis:
                raise ScopeViolation(
                    "Shared wording requires a selected-variant benefit table or explicit applicability clause; generic benefit prose is insufficient."
                )
        if required_optional and unit.coverage_scope != "optional, extra premium":
            raise ScopeViolation(
                "Optional/add-on/rider cover must be labelled optional, extra premium; it is not base cover."
            )
        if not required_optional and unit.coverage_scope != "base":
            raise ScopeViolation("Optional scope has no original-source support.")
        return statement.model_copy(
            update={
                "coverage_scope": (
                    "optional premium adjustment"
                    if required_optional and re.search(r"discount", statement.text, re.I)
                    else unit.coverage_scope
                ),
                "scope_product": self.product,
                "scope_variant": self.variant,
            }
        )


class ScopedLabels(PacketLabels):
    def __init__(self, packet, scope):
        super().__init__(packet)
        self.scope = scope

    def payload(self):
        result = super().payload()
        result["schema_version"] = 3
        result["selected_product"] = self.scope.product
        result["selected_variant"] = self.scope.variant
        for p in result["passages"]:
            section, segment = self.passages[p["label"]]
            p["source_role"] = section.role
            p["scope"] = self.scope.context(section, segment, segment.text)
            if OPTIONAL.search(segment.text) and not p["scope"]["scope_headings"]:
                p["scope"]["coverage_scope"] = (
                    "mixed passage; resolve each selected clause separately"
                )
        for t in result["tables"]:
            t["scope"] = self.scope.table_scope(self.tables[t["label"]])
        return result


def closes_scope(root, other):
    left, right = root.split("."), other.split(".")
    if len(right) > len(left):
        return False
    if left[0].isalpha() != right[0].isalpha():
        return False
    return right != left and (len(right) == 1 or right[:-1] == left[: len(right) - 1])


_CACHE = OrderedDict()
_CACHE_LOCK = RLock()


def scope_for(bundle):
    # Only immutable production indexes are cached; synthetic test bundles are
    # deliberately uncached. No summary or navigation text enters this cache.
    if not bundle.get("documents"):
        return ScopeIndex(bundle)
    key = (bundle["index_id"], tuple(d["sha256"] for d in bundle["documents"]))
    with _CACHE_LOCK:
        if key in _CACHE:
            _CACHE.move_to_end(key)
            return _CACHE[key]
    value = ScopeIndex(bundle)
    with _CACHE_LOCK:
        _CACHE[key] = value
        if len(_CACHE) > 24:
            _CACHE.popitem(last=False)
    return value
