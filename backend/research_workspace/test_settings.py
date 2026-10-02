"""Legacy regression settings, excluded from the retrieval-demo runtime."""

import os
from pathlib import Path

from config.settings import *  # noqa: F403
from config.settings import COVERGUIDE_REPORT_ROOT

AI_RELAY_MANAGEMENT_KEY = os.environ.get("AI_RELAY_MANAGEMENT_KEY", "")
AI_RELAY_STATE_DIR = Path(
    os.environ.get("AI_RELAY_STATE_DIR", "~/.local/state/job-in/relay-accounts")
).expanduser()
# Optional OmniRoute gateway (self-hosted, loopback only). Off unless explicitly enabled and the
# operator confirms request logging is disabled on the gateway key. ``OMNIROUTE_MODELS`` is a comma
# list of ``requested-id=expected-reported-id`` pairs, e.g. ``gemini/x=x``.
OMNIROUTE_ENABLED = os.environ.get("OMNIROUTE_ENABLED", "0") == "1"
OMNIROUTE_BASE_URL = os.environ.get("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128")
OMNIROUTE_API_KEY = os.environ.get("OMNIROUTE_API_KEY", "")
OMNIROUTE_LOGGING_DISABLED_CONFIRMED = (
    os.environ.get("OMNIROUTE_LOGGING_DISABLED_CONFIRMED", "0") == "1"
)
OMNIROUTE_MODELS = os.environ.get("OMNIROUTE_MODELS", "")
# Explicit local-only acceptance for sending real pilot conversation data through an upstream
# provider. It is rejected outside DEBUG even when every gateway transport check passes.
COVERGUIDE_LOCAL_OMNIROUTE_PILOT_ACK = (
    os.environ.get("COVERGUIDE_LOCAL_OMNIROUTE_PILOT_ACK", "0") == "1"
)
AI_TURN_TIMEOUT_SECONDS = int(os.environ.get("AI_TURN_TIMEOUT_SECONDS", "240"))

COVERGUIDE_CUSTOMER_INTERPRETATION_MODEL = os.environ.get(
    "COVERGUIDE_CUSTOMER_INTERPRETATION_MODEL", "gpt-5.6-luna"
)
COVERGUIDE_POLICY_EXTRACTION_MODEL = "gpt-5.6-sol"
COVERGUIDE_POLICY_REVIEW_MODEL = "gpt-5.6-terra"
# Applied only to manifest-v2 criterion extraction; other routes keep their defaults.
COVERGUIDE_POLICY_EXTRACTION_REASONING_EFFORT = os.environ.get(
    "COVERGUIDE_POLICY_EXTRACTION_REASONING_EFFORT", "low"
)
COVERGUIDE_POLICY_EXTRACTION_MAX_OUTPUT_TOKENS = int(
    os.environ.get("COVERGUIDE_POLICY_EXTRACTION_MAX_OUTPUT_TOKENS", "8192")
)
COVERGUIDE_COMPARISON_MODEL = os.environ.get("COVERGUIDE_COMPARISON_MODEL", "gpt-5.6-sol")
# Optional OmniRoute override for the two interactive roles only: ``omniroute:<requested id>``,
# which must appear in OMNIROUTE_MODELS. Empty keeps the relay model above.
COVERGUIDE_CUSTOMER_INTERPRETATION_ROUTE = os.environ.get(
    "COVERGUIDE_CUSTOMER_INTERPRETATION_ROUTE", ""
)
COVERGUIDE_COMPARISON_ROUTE = os.environ.get("COVERGUIDE_COMPARISON_ROUTE", "")

# Measured local raw-evidence path; it never needs a dense qualification for BM25.
COVERGUIDE_EVIDENCE_RETRIEVAL = os.environ.get("COVERGUIDE_EVIDENCE_RETRIEVAL", "pageindex")
COVERGUIDE_EVIDENCE_TOKEN_BUDGET = int(os.environ.get("COVERGUIDE_EVIDENCE_TOKEN_BUDGET", "16000"))
COVERGUIDE_PAGEINDEX_TREE_ROOT = Path(os.environ.get(
    "COVERGUIDE_PAGEINDEX_TREE_ROOT", str(COVERGUIDE_REPORT_ROOT / "retrieval-benchmark" / "pageindex-trees")
))
