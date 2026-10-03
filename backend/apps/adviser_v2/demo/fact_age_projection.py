"""Age bounds must share a printed person clause; proximity is not applicability."""

import re


def project_ages(statements, variant):
    rules = []
    unit = r"(?:days?|months?|years?)"
    bounds = re.compile(
        r"(\d+)\s*(" + unit + r")?\s*(?:to|and|[-–])\s*(\d+)\s*(" + unit + r")", re.I
    )
    for statement in statements:
        for cite in statement["citations"]:
            # Explicit two-axis minimum/maximum tables are paired by the
            # printed Adult/Child labels, never by nearby numbers.
            table_raw = " ".join(cite["quote"].split())
            from .fact_fit_projection import rule_for

            for row in re.finditer(
                r"For (Adults?|Dependent Child(?:ren)?)\s*[-–:]\s*Minimum\s*[-–:]?\s*(\d+)\s*(days?|months?|years?)\s*(?:&|and)\s*Maximum\s*[-–:]?\s*(?:Up to\s*)?(\d+)\s*(days?|months?|years?)",
                table_raw,
                re.I,
            ):
                relation = "adult" if row[1].lower().startswith("adult") else "child"
                u1, u2 = row[3].lower().rstrip("s") + "s", row[5].lower().rstrip("s") + "s"
                rules.append(
                    rule_for(
                        statement,
                        "entry_age",
                        "age",
                        f"{row[2]}:{u1}:{row[4]}:{u2}",
                        variant,
                        row[0],
                        minimum=int(row[2]),
                        minimum_unit=u1,
                        maximum=int(row[4]),
                        maximum_unit=u2,
                        relationship=relation,
                        inclusive=True,
                    )
                )
            for relation, label in [
                ("adult", r"adults?"),
                ("child", r"(?:dependent )?child(?:ren)?"),
            ]:
                lower = re.findall(
                    r"minimum entry age(?: limit)?[^.]{0,100}? for "
                    + label
                    + r" (?:is|in this product is) (\d+)\s*(days?|months?|years?)",
                    table_raw,
                    re.I,
                )
                upper = re.findall(
                    r"maximum entry age(?: limit| allowed)? for "
                    + label
                    + r"(?: in this product)? is (\d+)\s*(days?|months?|years?)",
                    table_raw,
                    re.I,
                )
                if len(set(lower)) == 1 and len(set(upper)) == 1:
                    lo, u1 = lower[0]
                    hi, u2 = upper[0]
                    u1, u2 = u1.lower().rstrip("s") + "s", u2.lower().rstrip("s") + "s"
                    rules.append(
                        rule_for(
                            statement,
                            "entry_age",
                            "age",
                            f"{lo}:{u1}:{hi}:{u2}",
                            variant,
                            table_raw,
                            minimum=int(lo),
                            minimum_unit=u1,
                            maximum=int(hi),
                            maximum_unit=u2,
                            relationship=relation,
                            inclusive=True,
                        )
                    )
            # General individual entry eligibility is distinct from the
            # proposer age and from the following child-only floater clause.
            general = re.search(
                r"offered to an individual with minimum age of (\d+) years \(Proposer[^)]*\)\. Maximum entry age is up to (\d+) years",
                table_raw,
                re.I,
            )
            if general:
                rules.append(
                    rule_for(
                        statement,
                        "entry_age",
                        "age",
                        f"{general[1]}:years:{general[2]}:years",
                        variant,
                        general[0],
                        minimum=int(general[1]),
                        minimum_unit="years",
                        maximum=int(general[2]),
                        maximum_unit="years",
                        relationship="person",
                        inclusive=True,
                    )
                )
            low_head = re.search(r"Entry Age\s*[:–-]\s*Minimum", table_raw, re.I)
            high_head = re.search(r"Entry Age\s*[:–-]\s*Maximum", table_raw, re.I)
            if low_head and high_head and low_head.end() < high_head.start():
                low_block = table_raw[low_head.end() : high_head.start()]
                high_block = re.split(
                    r"\b(?:Exit Age|Age of Proposer|Policy Term)\b",
                    table_raw[high_head.end() :],
                    maxsplit=1,
                    flags=re.I,
                )[0]
                for relation in ("adult", "child"):
                    pattern = r"\b" + relation + r"\s*[-–:]?\s*(\d+)\s*(days?|months?|years?)"
                    lows = re.findall(pattern, low_block, re.I)
                    highs = re.findall(pattern, high_block, re.I)
                    unlimited = re.search(
                        r"\b" + relation + r"\s*[-–:]?\s*(?:Lifelong|No Limit)", high_block, re.I
                    )
                    if len(lows) == 1 and unlimited:
                        lo, u1 = lows[0]
                        rules.append(
                            rule_for(
                                statement,
                                "entry_age",
                                "age",
                                f"{lo}:{u1}:unbounded",
                                variant,
                                table_raw,
                                minimum=int(lo),
                                minimum_unit=u1.lower().rstrip("s") + "s",
                                maximum_unbounded=True,
                                relationship=relation,
                                inclusive=True,
                            )
                        )
                        continue
                    if len(lows) != 1 or len(highs) != 1:
                        continue
                    minimum, u1 = int(lows[0][0]), lows[0][1].lower().rstrip("s") + "s"
                    maximum, u2 = int(highs[0][0]), highs[0][1].lower().rstrip("s") + "s"
                    rules.append(
                        {
                            "field": "entry_age",
                            "kind": "age",
                            "value": f"{minimum}:{u1}:{maximum}:{u2}",
                            "printed": table_raw,
                            "minimum": minimum,
                            "minimum_unit": u1,
                            "maximum": maximum,
                            "maximum_unit": u2,
                            "maximum_unbounded": False,
                            "inclusive": True,
                            "relationship": relation,
                            "variant": variant,
                            "scope": "base",
                            "citations": [
                                c
                                for item in [
                                    statement,
                                    *statement.get("conditions", []),
                                    *statement.get("restrictions", []),
                                ]
                                for c in item["citations"]
                            ],
                            "conditions": [
                                i["text"]
                                for i in [
                                    *statement.get("conditions", []),
                                    *statement.get("restrictions", []),
                                ]
                            ],
                            "condition_mode": "quoted",
                            "guards": [],
                            "supported": True,
                        }
                    )
                continue
            # Bullet/sentence boundaries prevent mixing an adult minimum with
            # a dependent child's upper bound elsewhere in the quotation.
            chunks = re.split(
                r"[▪•➢]|(?<=[.!?])\s+(?=[A-Z])|[;\n]\s*(?=(?:(?:Dependent )?(?:Adults?|Child(?:ren)?)|Renewal)\b)",
                cite["quote"],
            )
            for chunk in chunks:
                raw = " ".join(chunk.split())
                if not re.search(r"age|adult|child|eligible", raw, re.I):
                    continue
                if re.search(
                    r"provided|only|proposer|renewal|attains|more than|below|above 65", raw, re.I
                ):
                    continue
                relationships = set(
                    re.findall(r"\badults?\b|\bchild(?:ren)?\b|\bpersons?\b", raw, re.I)
                )
                kinds = {
                    "adult"
                    if v.lower().startswith("adult")
                    else "child"
                    if v.lower().startswith("child")
                    else "person"
                    for v in relationships
                }
                if len(kinds) != 1:
                    first_range = bounds.search(raw)
                    preceding = raw[: first_range.start()] if first_range else ""
                    subjects = re.findall(r"\b(adult|child(?:ren)?|person)s?\b", preceding, re.I)
                    if subjects and len(set(v.lower() for v in subjects)) == 1:
                        subject = subjects[0].lower()
                        kinds = {"child" if subject.startswith("child") else subject}
                    else:
                        continue
                relationship = kinds.pop()
                low = re.search(
                    r"minimum (?:entry )?age[^;]{0,110}?(\d+)\s*(" + unit + ")", raw, re.I
                )
                high = re.search(
                    r"maximum (?:entry )?age[^.;]{0,45}?(\d+)\s*(" + unit + ")", raw, re.I
                )
                unlimited = re.search(
                    r"no (?:limit on )?maximum (?:entry )?age|no upper age limit", raw, re.I
                )
                candidates = []
                if low and (high or unlimited):
                    candidates.append(
                        (
                            int(low[1]),
                            low[2],
                            int(high[1]) if high else None,
                            high[2] if high else None,
                            raw,
                            bool(unlimited),
                        )
                    )
                else:
                    onward = re.search(
                        r"(?:Adults?|Persons?).{0,25}?(\d+)\s*(years?)\s*(?:onwards|and above|to (?:Lifelong|Unlimited|No Limit))",
                        raw,
                        re.I,
                    )
                    if onward and not re.search(r"renew", raw, re.I):
                        candidates.append((int(onward[1]), onward[2], None, None, raw, True))
                    candidates.extend(
                        (int(m[1]), m[2] or m[4], int(m[3]), m[4], raw, False)
                        for m in bounds.finditer(raw)
                    )
                for minimum, u1, maximum, u2, printed, unbounded in candidates:
                    u1 = u1.lower().rstrip("s") + "s"
                    u2 = u2.lower().rstrip("s") + "s" if u2 else None
                    if maximum is not None and u1 == u2 and minimum > maximum:
                        continue
                    rules.append(
                        {
                            "field": "entry_age",
                            "kind": "age",
                            "value": f"{minimum}:{u1}:{maximum}:{u2}",
                            "printed": printed,
                            "minimum": minimum,
                            "minimum_unit": u1,
                            "maximum": maximum,
                            "maximum_unit": u2,
                            "maximum_unbounded": unbounded,
                            "inclusive": True,
                            "relationship": relationship,
                            "variant": variant,
                            "scope": "base",
                            "citations": [
                                c
                                for item in [
                                    statement,
                                    *statement.get("conditions", []),
                                    *statement.get("restrictions", []),
                                ]
                                for c in item["citations"]
                            ],
                            "conditions": [
                                item["text"]
                                for item in [
                                    *statement.get("conditions", []),
                                    *statement.get("restrictions", []),
                                ]
                            ],
                            "condition_mode": "quoted",
                            "guards": [],
                            "supported": True,
                        }
                    )
    distinct = {}
    for rule in rules:
        key = (rule["relationship"], rule["value"])
        if key not in distinct:
            distinct[key] = rule
        else:
            for citation in rule["citations"]:
                if citation not in distinct[key]["citations"]:
                    distinct[key]["citations"].append(citation)
    return list(distinct.values())
