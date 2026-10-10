"""Source-only product, variant and optional-cover gates for displayed answers."""

import re
import unicodedata
from bisect import bisect_right
from collections import Counter, OrderedDict
from threading import RLock

from .assembly import (
    EvidenceInsufficient,
    PacketLabels,
    UnknownLabel,
    document_source,
    locate_passage,
)
from .evidence import Section
from .quotations import normalized
from .table_cells import aligned, fields

SCOPE_VERSION = "original-scope/1"
OPTIONAL = re.compile(
    r"\boptional\b|\badd[ -]?ons?\b|\briders?\b|\bextra premium\b|\badditional premium\b",
    re.I,
)
# A variant table may offer a cover for extra payment without the word "optional".
PAY_EXTRA = re.compile(r"\bchoose to\b|\bpay\b[^.;]{0,40}\b(?:additional|extra)\b", re.I)
# Wording that gives a cover only to those who choose it ("If opted, you can avail Air
# Ambulance", "can only be opted for Classic & Select Variants") supports an optional
# label; a passing "(if opted)" about other covers does not.
OPTED = re.compile(r"(?<!\()\bif opted\b|\bcan (?:only )?be opted\b", re.I)
# A clause limiting wording to the variants it names (see `applies_to`).
APPLIES = re.compile(
    r"(?<!not )\b(?:applicable|available|covered|opted)\s+(?:under|for|to)\s+([^.;\n]{1,100})",
    re.I,
)
TOPICS = {
    "icu": r"\bICU\b|intensive care",
    "day_care": r"day[ -]?care",
    "road_ambulance": r"road ambulance|(?<!air )(?<!air-)\bambulance",
    "pre_post": r"pre\s*-?\s*(?:and post\s*-?\s*)?hospitali[sz]ation|post\s*-?\s*hospitali[sz]ation",
    "organ_donor": r"organ donor|donor expenses|organ transplant",
    "home_care": r"domiciliary|home[ -]?(?:health[ -]?)?care|treatment at home",
    "ped": r"pre[ -]?existing|\bPED\b|Excl\s*0?1\b",
    "specified_waiting": r"specifi(?:ed|c) (?:disease|illness|waiting)|Excl\s*0?2\b",
    "deductible": r"deductible",
    "copay": r"co[ -]?pay(?:ment)?",
    "room": r"room|boarding|accommodation",
    "maternity": r"maternity|delivery|deliveries|childbirth",
    "newborn": r"new[ -]?born",
    "opd": r"out[ -]?patient|\bOPD\b|consultation",
    "restoration": r"restor|recharg|reload|reinstate|\breset\b",
    "bonus": r"bonus|no[ -]?claim|booster|super credit|carr(?:y|ies) forward",
    "ayush": r"AYUSH|Ayurveda|Unani|Siddha|Homeopath",
    "air_ambulance": r"air ambulance",
    "health_check": r"health[ -]?check|check[ -]?up",
    "cataract": r"cataract",
    "sum_insured": r"sum insured (?:options|choices)|base sum insured",
}


class ScopeViolation(EvidenceInsufficient):
    pass


def canon(value):
    # A heading wrapped before its "+" ("VIP +") names the same variant as "VIP+".
    return re.sub(r"\s+\+$", "+", " ".join(value.split())).casefold()


def named(text, name):
    return bool(re.search(r"(?<!\w)" + re.escape(canon(name)) + r"(?![\w+])", canon(text)))


def printed_name(text, name):
    """`named`, except that a capitalised name met only in lowercase prose is an
    ordinary word ("select network hospitals" doesn't name the Select variant)."""
    if not named(text, name):
        return False
    if not any(c.isupper() for c in name):
        return True
    pattern = r"(?<!\w)" + r"\s+".join(map(re.escape, name.split())) + r"(?![\w+])"
    return any(not m[0].islower() for m in re.finditer(pattern, text, re.I))


def plain(text):
    """Topic matching reads PDF ligatures as plain text."""
    return unicodedata.normalize("NFKC", text)


def applies_to(text, variant):
    """Whether a clause limiting wording to the variants it names ("can only be opted
    for Classic &\nSelect Variants") names this variant, with wrapped lines joined."""
    return bool(variant) and any(
        printed_name(c, variant) for c in APPLIES.findall(" ".join(plain(text).split()))
    )


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
    if re.fullmatch(
        r"Optional (?:Packages?|Covers?|Benefits)(?:\s*\([^)]{1,100}\))?[:]?", title, re.I
    ):
        return True
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

        def printing(cells):
            return any(
                named(c["text"], v) or canon(v) in canon(c["text"])
                for c in cells
                for v in self.names
            )

        for table in bundle.get("tables", []):
            cells = list(table["cells"].values())
            headers = [c for c in cells if c["row"] <= 2 and len(c["text"].split()) <= 5]
            if printing(headers):
                # Further variant names come only from a first row that prints a known
                # variant; otherwise that row holds values such as "Covered". A wrapped
                # heading's first line printed over several columns ("Optima" over each
                # Optima column) names none of them.
                top = [c for c in headers if c["column"] > 0 and c["row"] == 0]
                if not printing(top):
                    top = []
                printed = Counter(canon(c["text"]) for c in top)
                candidates = {
                    " ".join(c["text"].split())
                    for c in top
                    if printed[canon(c["text"])] == 1
                    and not re.search(
                        r"\d|%|insured|waiting|period|benefit|section|plan[s]?\b|coverage|limit"
                        r"|\btitle\b|clause|description|particulars|optional|covers?\b|features?"
                        r"|\bper\b|check[ -]?up|\bs\.?\s*no\b|\bsr\b|\bname\b|options?\b",
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
        key = (section.document_id, section.document_sha256)
        raw = self.documents[key]
        start, end = locate_passage(section, segment, quote, occurrence, raw)
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
        local = raw[start:end]
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
        owners = [
            m
            for m in prior
            if any(canon(m["title"]) == canon(v) for v in self.names)
            and not table_cell_line(raw, m)
        ]
        if owners:
            owner = owners[-1]
            later = [m for m in prior if m.start() > owner.start() and m["number"]]
            # An unnumbered variant title owns only the text before the next
            # numbered clause; a numbered one, until a sibling or parent clause.
            closed = (
                any(closes_scope(owner["number"], m["number"]) for m in later)
                if owner["number"]
                else bool(later)
            )
            if not closed:
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

    def optional_rows(self, table):
        """Rows of a variant table that fall inside an "Optional Covers" section.

        Rows below an in-table marker are optional. A table continuing on the next
        page under the same header starts inside the section its previous page ended
        in, down to its first heading row (one holding a single cell, such as
        "Waiting Period").
        """
        counts = Counter(c["row"] for c in table["cells"].values())
        marks = self.table_scope(table)["optional_rows_after"]
        rows = {r for r in counts if any(r > m for m in marks)}
        if self.continues_optional(table):
            end = min((r for r in counts if counts[r] == 1), default=max(counts) + 1)
            rows |= {r for r in counts if 0 < r < end}  # Row 0 repeats the header.
        return rows

    def continues_optional(self, table):
        parts = table["id"].rsplit(":", 2)  # "<document sha>:<page>:<n-th table on page>"
        if len(parts) != 3 or parts[2] != "0" or not parts[1].isdigit():
            return False
        document, page, _ = parts
        before = [
            t
            for t in self.table_map.values()
            if t["id"] in self.matrices and t["id"].startswith(f"{document}:{int(page) - 1}:")
        ]
        if not before:
            return False
        previous = max(before, key=lambda t: int(t["id"].rsplit(":", 1)[1]))

        def header(t):
            return [
                canon(c["text"])
                for c in sorted(t["cells"].values(), key=lambda c: c["column"])
                if c["row"] == 0
            ]

        last = max(c["row"] for c in previous["cells"].values())
        return header(previous) == header(table) and last in self.optional_rows(previous)

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
        raw = plain(" ".join(main))
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
                # A variant's own cell may label its fields ("Road Ambulance: Unlimited")
                # under a row label that names neither ("Expenses in Reaching the Hospital").
                printed = list(fields(value["text"])) if matrix and value else []
                axis_text = plain(" ".join([*(c["text"] for c in axes), *printed]))
                if topics and not any(re.search(TOPICS[k], axis_text, re.I) for k in topics):
                    raise ScopeViolation(
                        "Table axes do not identify the requested benefit or field."
                    )
                if matrix and not any(canon(c["text"]) in self.aliases for c in axes):
                    raise ScopeViolation(
                        "Shared table requires the selected variant/product axis, not another plan column."
                    )
                table_proven = bool(matrix)
                optional_rows = self.table_scope(table)["optional_rows_after"]
                if matrix and value:
                    # The selected variant's own cell decides its scope. Wording shared
                    # by a product family may file a benefit under optional covers that
                    # this variant's column includes, or mention optional covers in passing.
                    rows = [table["cells"][k] for k in support.row_label_ids if k in table["cells"]]
                    required_optional = any(
                        optional_cover(c["text"]) or PAY_EXTRA.search(c["text"])
                        for c in [value, *rows]
                    ) or value["row"] in self.optional_rows(table)
                elif value and any(value["row"] > r for r in optional_rows):
                    required_optional = True
        shared_topics = {k for t in self.matrices.values() for k in t["topics"]}
        if any(k in shared_topics for k in topics) and not table_proven and not exclusion(raw):
            named_selected = applies_to(
                " ".join(r.quote for r in [*unit.benefit, *unit.conditions, *unit.restrictions]),
                self.variant,
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
        if not required_optional and unit.coverage_scope != "base" and not OPTED.search(raw):
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
            table = self.tables[t["label"]]
            t["scope"] = self.scope.table_scope(table)
            if table["id"] in self.scope.matrices and self.scope.continues_optional(table):
                t["scope"]["optional_rows_continued_from_previous_page"] = sorted(
                    self.scope.optional_rows(table)
                )
        return result

    def table_ref(self, ref):
        region = self.tables.get(ref.table)
        if region is None or region["id"] not in self.scope.matrices:
            return super().table_ref(ref)
        return region, variant_ref(ref, self.cells[ref.table], region, self.scope.aliases)


def squeezed(text):
    return "".join(ch for ch in normalized(text)[0].casefold() if ch.isalnum())


def variant_ref(ref, mapping, region, aliases):
    """A variant-table reference named by alias or printed text. Models also join
    adjacent cells ("1.1.b — ICU") and add the table's other headings, so only the
    labels aligned with the value are kept, and repeated value text is read under
    the selected variant's column. A value may also be one field a cell prints
    ("Road Ambulance: INR 2000"), with or without its label; the whole cell is
    cited. Validation still checks every kept label."""
    cells = {alias: region["cells"][key] for alias, key in mapping.items()}

    def flat(text):
        return " ".join(normalized(text)[0].split()).casefold()

    def printing(text):
        """The cells printing this text as one of their own fields."""
        wanted = flat(text)
        return [
            [alias]
            for alias, c in cells.items()
            if wanted
            and any(
                wanted in {flat(f"{label}: {entry}"), flat(entry)}
                for label, entry in fields(c["text"]).items()
            )
        ]

    def meanings(text):
        if text in cells:
            return [[text]]
        wanted = flat(text)
        exact = [
            [alias]
            for alias, c in cells.items()
            if wanted in {flat(t) for t in (c["text"], c["citation"]["quote"])}
        ]
        key = squeezed(text)
        if exact or not key:
            return exact
        joined = []
        for row in sorted({c["row"] for c in cells.values()}):
            line = sorted((c["column"], alias) for alias, c in cells.items() if c["row"] == row)
            for i in range(len(line)):
                for j in range(i + 2, len(line) + 1):
                    if "".join(squeezed(cells[a]["text"]) for _, a in line[i:j]) == key:
                        joined.append([a for _, a in line[i:j]])
        return joined

    def kept(texts, at, same):
        """The cells these texts name that share the value's row (or column) and
        precede it; a text with no single such meaning is dropped."""
        result = []
        for text in texts:
            groups = [g for g in meanings(text) if all(aligned(cells[a], at, same) for a in g)]
            if len(groups) == 1:
                result.extend(a for a in groups[0] if a not in result)
        return result

    options = []
    for value in [g[0] for g in meanings(ref.value) or printing(ref.value) if len(g) == 1]:
        at = cells[value]
        rows = kept(ref.rows, at, "row")
        columns = kept(ref.columns, at, "column")
        if rows and columns:
            options.append((value, rows, columns))
    if len(options) > 1:
        options = [o for o in options if any(canon(cells[a]["text"]) in aliases for a in o[2])]
    if len(options) != 1:
        raise UnknownLabel("Unknown packet table/cell label.")
    value, rows, columns = options[0]
    return ref.model_copy(update={"value": value, "rows": rows, "columns": columns})


def table_cell_line(raw, match):
    """A short line between other short lines is a flattened table cell, such
    as a variant column header, not a section title that owns later text."""
    before = raw[: match.start()].rstrip().rsplit("\n", 1)[-1].strip()
    after = raw[match.end() :].lstrip().split("\n", 1)[0].strip()
    return any(
        0 < len(line.split()) <= 2 or (len(line.split()) == 3 and not line.endswith("."))
        for line in (before, after)
    )


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
