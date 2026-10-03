from dataclasses import replace

from apps.adviser_v2.demo.fact_packet_recovery import recover
from apps.adviser_v2.tests.test_demo_contracts import packet


def fixture(text):
    pkt = packet(text)
    segment = replace(
        pkt.sections[0].segments[0],
        start=0,
        end=len(text),
        document_start=0,
        document_end=len(text),
    )
    section = replace(pkt.sections[0], segments=(segment,))
    pkt = replace(pkt, sections=(section,))
    bundle = {
        "policy_version_id": "plan",
        "variant": "Default",
        "variants": [],
        "sections": [section.payload()],
    }
    return {"packet": pkt.evidence(), "index_version": "index"}, bundle


def test_recovery_requires_retrieved_original_text_and_keeps_six_checks():
    result, bundle = fixture(
        "Coverage\nThe Company will indemnify the Insured Person for Hospitalization expenses.\n"
    )
    found = recover(result, "plan_type", bundle)
    assert len(found) == 1 and all(found[0]["checks"])
    assert found[0]["projection_method"] == "literal_card_clause_recovery"
    empty = {**result, "packet": {**result["packet"], "sections": []}}
    assert not recover(empty, "plan_type", bundle)
    bundle["navigation"] = [{"summary": "Both indemnity and Benefit"}]
    assert not recover(empty, "plan_type", bundle)


def test_premium_tier_continuation_stops_at_next_sibling():
    result, bundle = fixture(
        "1.24. Premium Tier\nThe premium is computed based on city of residence.\nTier 1: Delhi.\nTier 2: Rest of India.\n1.25. Renewal\nRenewal rules follow.\n"
    )
    found = recover(result, "geography", bundle)
    assert len(found) == 1 and all(found[0]["checks"])
    quotes = [c["quote"] for c in found[0]["answer"]["statements"][0]["citations"]]
    assert "Rest of India" in "".join(quotes) and "Renewal rules" not in "".join(quotes)


def test_outpatient_list_item_keeps_nonpayment_introduction():
    result, bundle = fixture(
        "3. Specific Exclusions:\nThe Company shall not make any payment for the following:\na. War.\nl. Treatment taken on outpatient basis.\nm. Spectacles.\n"
    )
    found = recover(result, "opd", bundle)
    assert len(found) == 1 and all(found[0]["checks"])
    quotes = [c["quote"] for c in found[0]["answer"]["statements"][0]["citations"]]
    assert len(quotes) == 2
    assert "shall not make any payment" in quotes[0]
    assert "outpatient" in quotes[1]
    assert "War" not in "".join(quotes)
