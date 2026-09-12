"""Single-call Responses boundary. Provider text and credentials never enter errors."""

import asyncio
import ipaddress
import json
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

MAX_RESPONSE_BYTES = 262_144
PROFILE_FIELDS = (
    "members",
    "location",
    "existing_cover",
    "budget",
    "medical_information",
    "priorities",
)


class ClaimDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_id: str
    display_text: str
    claim_type: Literal[
        "policy_fact",
        "source_attribution",
        "calculation",
        "recommendation_inference",
        "user_profile_reference",
    ]
    fact_ids: list[str]
    evidence_bundle_ids: list[str]
    conditions: list[str]
    note: str | None


class StructuredAnswerDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    outcome: Literal["answer", "needs_input", "insufficient_evidence"]
    introduction: str
    claims: list[ClaimDraft]
    follow_up: str | None


class ProfileFieldDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: Literal[
        "members", "location", "existing_cover", "budget", "medical_information", "priorities"
    ]
    value: str


class InterviewDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fields: list[ProfileFieldDraft]


@dataclass(frozen=True)
class RelayRoute:
    relay_type: Literal["cliproxyapi", "omniroute"]
    base_url: str
    model: str
    api_dialect: Literal["openai_responses"]
    context_limit: int
    timeout_seconds: float
    qualified: bool


class RelayFailure(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def loopback_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        host = parsed.hostname or ""
        valid = ipaddress.ip_address(host).is_loopback
        if (
            not valid
            or parsed.scheme != "http"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in ("", "/", "/v1", "/v1/")
            or not parsed.port
        ):
            raise ValueError
    except ValueError as exc:
        raise RelayFailure(
            "invalid_relay_url", "The relay must use a literal loopback HTTP address and port."
        ) from exc
    return f"http://{parsed.netloc}"


def validate_strict_schema(schema: dict[str, Any]) -> None:
    """Check every nested object, including objects inside definitions and unions."""

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" or "properties" in node:
                properties = node.get("properties", {})
                if (
                    not isinstance(properties, dict)
                    or node.get("additionalProperties") is not False
                    or set(node.get("required", [])) != set(properties)
                ):
                    raise RelayFailure(
                        "invalid_schema",
                        "Every schema property must be required; extra properties must be forbidden.",
                    )
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(schema)


class StrictRelayAdapter:
    def __init__(self, route: RelayRoute, client: httpx.AsyncClient, credential: str):
        if not route.qualified:
            raise RelayFailure(
                "route_unqualified", "The selected model is not currently qualified."
            )
        if route.relay_type != "cliproxyapi" or route.api_dialect != "openai_responses":
            raise RelayFailure("unsupported_route", "This route is not enabled.")
        self.base_url = loopback_url(route.base_url)
        if not credential:
            raise RelayFailure("relay_unconfigured", "The relay is not configured.")
        self.route, self.client, self.credential = route, client, credential
        self.reported_model = ""
        self.usage: dict[str, int] = {}

    async def generate[T: BaseModel](
        self,
        canonical_messages: list[dict[str, str]],
        remaining_deadline: float,
        output_type: type[T],
    ) -> T:
        if remaining_deadline <= 0:
            raise RelayFailure("deadline_exceeded", "The turn deadline has expired.")
        schema = output_type.model_json_schema()
        validate_strict_schema(schema)
        # Conservative byte bound: reject the whole history, never truncate it.
        if (
            len(json.dumps(canonical_messages, ensure_ascii=False).encode())
            + len(json.dumps(schema).encode())
            > self.route.context_limit
        ):
            raise RelayFailure(
                "context_limit",
                "This conversation is too long for the selected model. Start a new conversation.",
            )
        payload = {
            "model": self.route.model,
            "input": canonical_messages,
            "stream": False,
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": output_type.__name__,
                    "strict": True,
                    "schema": schema,
                }
            },
        }
        try:
            async with asyncio.timeout(min(self.route.timeout_seconds, remaining_deadline)):
                async with self.client.stream(
                    "POST",
                    f"{self.base_url}/v1/responses",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.credential}"},
                    follow_redirects=False,
                    timeout=min(self.route.timeout_seconds, remaining_deadline),
                ) as response:
                    codes = {
                        429: ("provider_quota", "The selected model reported quota exhaustion."),
                        404: ("model_missing", "The selected model is unavailable."),
                    }
                    if response.is_redirect:
                        raise RelayFailure(
                            "provider_redirect", "The relay returned an unsupported redirect."
                        )
                    if response.status_code in codes:
                        code, message = codes[response.status_code]
                        raise RelayFailure(code, message, response.status_code == 429)
                    if response.status_code >= 400:
                        raise RelayFailure(
                            "provider_unavailable"
                            if response.status_code >= 500
                            else "provider_rejected",
                            "The selected model could not complete this request.",
                            response.status_code >= 500,
                        )
                    chunks, total = [], 0
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > MAX_RESPONSE_BYTES:
                            raise RelayFailure(
                                "response_too_large", "The relay response exceeded the size limit."
                            )
                        chunks.append(chunk)
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise RelayFailure(
                "provider_timeout", "The selected model did not respond in time.", True
            ) from exc
        except httpx.HTTPError as exc:
            raise RelayFailure("provider_transport", "The relay request failed.", True) from exc
        try:
            envelope = json.loads(b"".join(chunks))
            if not isinstance(envelope, dict):
                raise ValueError
        except (ValueError, UnicodeDecodeError) as exc:
            raise RelayFailure("malformed_response", "The relay returned invalid JSON.") from exc
        # Missing model identity is also a failure. Do not persist untrusted model strings.
        if envelope.get("model") != self.route.model:
            raise RelayFailure(
                "model_identity_mismatch", "The relay did not confirm the exact selected model."
            )
        self.reported_model = self.route.model
        if envelope.get("status") != "completed" or envelope.get("error"):
            raise RelayFailure(
                "incomplete_response", "The selected model did not finish its answer."
            )
        usage = envelope.get("usage", {})
        if isinstance(usage, dict):
            self.usage = {
                key: usage[key]
                for key in ("input_tokens", "output_tokens", "total_tokens")
                if type(usage.get(key)) is int and usage[key] >= 0
            }
        try:
            contents = [
                part["text"]
                for item in envelope["output"]
                if item.get("type") == "message"
                for part in item["content"]
                if part.get("type") == "output_text"
            ]
            if len(contents) != 1:
                raise ValueError
            return output_type.model_validate_json(contents[0])
        except (AttributeError, KeyError, TypeError, ValueError, ValidationError) as exc:
            raise RelayFailure(
                "invalid_structured_output", "The relay response did not match the required schema."
            ) from exc

    async def generate_structured_answer(
        self, canonical_messages: list[dict[str, str]], remaining_deadline: float
    ) -> StructuredAnswerDraft:
        return await self.generate(canonical_messages, remaining_deadline, StructuredAnswerDraft)
