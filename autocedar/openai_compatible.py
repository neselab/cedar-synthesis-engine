"""Native local-model client for OpenAI-compatible AutoCedar servers.

The primary API implements AutoCedar's provider-neutral generation contract
over the portable Chat Completions endpoint exposed by vLLM and similar
servers.  A legacy ``messages`` shim remains only for older integrations.
"""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Callable, Sequence, TypeVar

from pydantic import BaseModel

from autocedar.providers.base import (
    ChatMessage,
    InstructionPart,
    ModelUsage,
    StructuredResult,
    TextResult,
)


DEFAULT_OPENAI_BASE_URL = "http://127.0.0.1:8000/v1"
DEFAULT_OPENAI_MODEL = "autocedar-local"
OPENAI_COMPATIBLE_PROVIDERS = {
    "local",
    "openai-compatible",
    "openai_compatible",
    "vllm",
}

_JSONRequester = Callable[
    [str, str, dict[str, str], Any | None, float],
    tuple[int, Any],
]


class OpenAICompatibleError(RuntimeError):
    """Raised when the configured compatible endpoint cannot respond."""


@dataclass(frozen=True)
class OpenAICompatibleRuntimeInfo:
    provider: str
    model: str
    base_url: str
    available: bool
    models: list[str] = field(default_factory=list)
    error: str | None = None


def is_openai_compatible_provider(provider: str | None) -> bool:
    return (provider or "").strip().lower() in OPENAI_COMPATIBLE_PROVIDERS


def openai_base_url() -> str:
    return (
        os.environ.get("AUTOCEDAR_LOCAL_BASE_URL", "").strip().rstrip("/")
        or DEFAULT_OPENAI_BASE_URL
    )


def openai_model() -> str:
    return (
        os.environ.get("AUTOCEDAR_LOCAL_MODEL", "").strip()
        or os.environ.get("AUTOCEDAR_MODEL", "").strip()
        or os.environ.get("AUTOCEDAR_AUTHOR_MODEL", "").strip()
        or os.environ.get("AUTOCEDAR_CHAT_MODEL", "").strip()
        or DEFAULT_OPENAI_MODEL
    )


def openai_api_key() -> str:
    """Return only the endpoint-specific key, never a cloud key implicitly."""

    return (
        os.environ.get("AUTOCEDAR_LOCAL_API_KEY", "").strip()
        or os.environ.get("AUTOCEDAR_OPENAI_API_KEY", "").strip()
    )


def list_openai_models(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    requester: _JSONRequester | None = None,
    timeout: float = 5.0,
) -> list[str]:
    requester = requester or _request_json
    resolved_base = (base_url or openai_base_url()).rstrip("/")
    status, payload = requester(
        "GET",
        f"{resolved_base}/models",
        _request_headers(api_key if api_key is not None else openai_api_key()),
        None,
        timeout,
    )
    if status != 200 or not isinstance(payload, dict):
        raise OpenAICompatibleError(_format_error(status, payload, resolved_base))
    entries = payload.get("data")
    if not isinstance(entries, list):
        raise OpenAICompatibleError(f"{resolved_base} returned no compatible model list.")
    models: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        model_id = entry.get("id")
        if isinstance(model_id, str) and model_id.strip() and model_id.strip() not in models:
            models.append(model_id.strip())
    if not models:
        raise OpenAICompatibleError(
            f"{resolved_base} is reachable but advertises no usable models.",
        )
    return models


def openai_runtime_info(
    *,
    requester: _JSONRequester | None = None,
    timeout: float = 3.0,
) -> OpenAICompatibleRuntimeInfo:
    base_url = openai_base_url()
    model = openai_model()
    try:
        models = list_openai_models(
            base_url=base_url,
            requester=requester,
            timeout=timeout,
        )
        return OpenAICompatibleRuntimeInfo(
            provider="local",
            model=model,
            base_url=base_url,
            available=True,
            models=models,
        )
    except Exception as exc:
        return OpenAICompatibleRuntimeInfo(
            provider="local",
            model=model,
            base_url=base_url,
            available=False,
            error=str(exc),
        )


_StructuredT = TypeVar("_StructuredT", bound=BaseModel)


class OpenAICompatibleClient:
    """Native AutoCedar client backed by ``/v1/chat/completions``.

    ``messages`` remains as a compatibility shim for older callers; new code
    uses :meth:`generate_text` and :meth:`generate_structured` directly.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        requester: _JSONRequester | None = None,
        timeout: float = 600.0,
    ) -> None:
        self.base_url = (base_url or openai_base_url()).rstrip("/")
        self.api_key = api_key if api_key is not None else openai_api_key()
        self._requester = requester or _request_json
        self.timeout = _configured_timeout(timeout)
        self.messages = _OpenAICompatibleMessages(self)

    def generate_text(
        self,
        *,
        model: str,
        messages: Sequence[ChatMessage],
        system: str | Sequence[InstructionPart] | None = None,
        max_tokens: int = 8192,
        temperature: float | None = None,
        reasoning_effort: str | None = None,
    ) -> TextResult:
        del reasoning_effort  # Portable Chat Completions has no common reasoning knob.
        payload = self._chat_payload(
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text, usage, response = self._decode(*self._request(payload))
        return TextResult(
            text=text,
            usage=usage,
            model=_response_string(response, "model") or model,
            request_id=_response_string(response, "id"),
        )

    def generate_structured(
        self,
        *,
        model: str,
        messages: Sequence[ChatMessage],
        output_type: type[_StructuredT],
        system: str | Sequence[InstructionPart] | None = None,
        max_tokens: int = 8192,
        temperature: float | None = None,
        reasoning_effort: str | None = None,
    ) -> StructuredResult[_StructuredT]:
        del reasoning_effort
        schema = output_type.model_json_schema()
        structured_messages = tuple(messages) + (
            ChatMessage(
                role="user",
                content=(
                    "Return only a JSON object matching this JSON Schema. Do not wrap "
                    "it in Markdown and do not include explanatory prose.\n\n"
                    f"{json.dumps(schema, indent=2, sort_keys=True)}"
                ),
            ),
        )
        payload = self._chat_payload(
            model=model,
            messages=structured_messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if _structured_output_mode() != "prompt":
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": output_type.__name__,
                    "schema": schema,
                },
            }
        status, response = self._request(payload)
        if "response_format" in payload and _structured_output_unsupported(status, response):
            payload = dict(payload)
            payload.pop("response_format", None)
            status, response = self._request(payload)
        text, usage, decoded = self._decode(status, response)
        try:
            parsed = output_type.model_validate(_extract_json_object(text))
        except Exception as exc:
            raise OpenAICompatibleError(
                f"Local model returned invalid {output_type.__name__} JSON: {exc}",
            ) from exc
        return StructuredResult(
            parsed=parsed,
            usage=usage,
            model=_response_string(decoded, "model") or model,
            request_id=_response_string(decoded, "id"),
        )

    def _chat_payload(
        self,
        *,
        model: str,
        messages: Sequence[ChatMessage],
        system: str | Sequence[InstructionPart] | None,
        max_tokens: int,
        temperature: float | None,
    ) -> dict[str, Any]:
        payload_messages: list[dict[str, str]] = []
        system_text = _render_provider_system(system)
        if system_text:
            payload_messages.append({"role": "system", "content": system_text})
        payload_messages.extend(
            {"role": message.role, "content": message.content}
            for message in messages
        )
        payload: dict[str, Any] = {
            "model": model or openai_model(),
            "messages": payload_messages,
            "stream": False,
            "max_tokens": _configured_max_tokens(max_tokens),
        }
        if temperature is not None:
            payload["temperature"] = float(temperature)
        return payload

    def _request(self, payload: dict[str, Any]) -> tuple[int, Any]:
        return self._requester(
            "POST",
            f"{self.base_url}/chat/completions",
            _request_headers(self.api_key, content_type="application/json"),
            payload,
            self.timeout,
        )

    def _decode(self, status: int, response: Any) -> tuple[str, ModelUsage, dict[str, Any]]:
        if status != 200 or not isinstance(response, dict):
            raise OpenAICompatibleError(_format_error(status, response, self.base_url))
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise OpenAICompatibleError(f"{self.base_url} returned no choices.")
        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise OpenAICompatibleError(f"{self.base_url} returned no message.")
        text = _render_content(message.get("content"))
        if not text.strip():
            raise OpenAICompatibleError(f"{self.base_url} returned an empty response.")
        return text, _extract_usage(response), response


class _OpenAICompatibleMessages:
    def __init__(self, parent: OpenAICompatibleClient) -> None:
        self._parent = parent

    def parse(self, **kwargs: Any) -> Any:
        output_format = kwargs.get("output_format")
        if not isinstance(output_format, type) or not issubclass(output_format, BaseModel):
            raise TypeError("OpenAICompatibleClient.parse requires a Pydantic output_format")
        result = self._parent.generate_structured(
            **_legacy_request_kwargs(kwargs),
            output_type=output_format,
        )
        return SimpleNamespace(parsed_output=result.parsed, usage=result.usage)

    def create(self, **kwargs: Any) -> Any:
        result = self._parent.generate_text(**_legacy_request_kwargs(kwargs))
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=result.text)],
            usage=result.usage,
        )


def _legacy_request_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    messages: list[ChatMessage] = []
    raw_messages = kwargs.get("messages")
    if isinstance(raw_messages, list):
        for message in raw_messages:
            if not isinstance(message, dict):
                continue
            role = str(message.get("role") or "user")
            if role == "developer":
                role = "system"
            if role not in {"user", "assistant", "system"}:
                role = "user"
            content = _render_content(message.get("content"))
            if content:
                messages.append(ChatMessage(role=role, content=content))  # type: ignore[arg-type]
    max_tokens = kwargs.get("max_tokens")
    temperature = kwargs.get("temperature")
    output_config = kwargs.get("output_config")
    effort = output_config.get("effort") if isinstance(output_config, dict) else None
    return {
        "model": str(kwargs.get("model") or openai_model()),
        "messages": tuple(messages),
        "system": _legacy_system(kwargs.get("system")),
        "max_tokens": (
            max_tokens
            if isinstance(max_tokens, int) and max_tokens > 0
            else 8192
        ),
        "temperature": (
            float(temperature)
            if isinstance(temperature, (int, float)) and not isinstance(temperature, bool)
            else None
        ),
        "reasoning_effort": effort if isinstance(effort, str) else None,
    }


def _legacy_system(value: Any) -> str | tuple[InstructionPart, ...] | None:
    if isinstance(value, str):
        return value or None
    if not isinstance(value, list):
        return None
    parts: list[InstructionPart] = []
    for item in value:
        if isinstance(item, str):
            if item:
                parts.append(InstructionPart(text=item))
            continue
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("content")
        if not isinstance(text, str) or not text:
            continue
        cache_hint = "ephemeral" if item.get("cache_control") else "none"
        parts.append(InstructionPart(text=text, cache_hint=cache_hint))
    return tuple(parts) or None


def _render_provider_system(
    system: str | Sequence[InstructionPart] | None,
) -> str:
    if isinstance(system, str):
        return system
    return "\n\n".join(part.text for part in (system or ()))


def _render_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return "" if content is None else str(content)
    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict):
            text = block.get("text") or block.get("content")
            if isinstance(text, str):
                parts.append(text)
        else:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                parts.append(text)
    return "\n\n".join(part for part in parts if part)


def _extract_json_object(text: str) -> Any:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(stripped[start : end + 1])


def _extract_usage(response: dict[str, Any]) -> ModelUsage:
    usage = response.get("usage") if isinstance(response.get("usage"), dict) else {}
    details = usage.get("prompt_tokens_details")
    cache_read = details.get("cached_tokens") if isinstance(details, dict) else 0
    return ModelUsage(
        input_tokens=_integer(usage.get("prompt_tokens")),
        output_tokens=_integer(usage.get("completion_tokens")),
        cache_read_input_tokens=_integer(cache_read),
    )


def _response_string(response: dict[str, Any], name: str) -> str | None:
    value = response.get(name)
    return value if isinstance(value, str) and value else None


def _integer(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(int(value), 0)
    return 0


def _structured_output_mode() -> str:
    return (
        os.environ.get("AUTOCEDAR_LOCAL_STRUCTURED_OUTPUT", "").strip()
        or os.environ.get("AUTOCEDAR_OPENAI_STRUCTURED_OUTPUT", "").strip()
        or "json_schema"
    ).lower()


def _structured_output_unsupported(status: int, payload: Any) -> bool:
    if status not in {400, 404, 422}:
        return False
    rendered = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)
    lowered = rendered.lower()
    return any(
        marker in lowered
        for marker in ("response_format", "json_schema", "structured output", "structured_output")
    )


def _configured_timeout(default: float) -> float:
    raw = (
        os.environ.get("AUTOCEDAR_LOCAL_TIMEOUT_SECONDS", "").strip()
        or os.environ.get("AUTOCEDAR_OPENAI_TIMEOUT_SECONDS", "").strip()
    )
    if not raw:
        return default
    try:
        return max(float(raw), 1.0)
    except ValueError:
        return default


def _configured_max_tokens(requested: int) -> int:
    """Apply an optional local-only output cap without changing cloud calls."""

    raw = os.environ.get("AUTOCEDAR_LOCAL_MAX_TOKENS", "").strip()
    if not raw:
        return requested
    try:
        configured = int(raw)
    except ValueError:
        return requested
    if configured <= 0:
        return requested
    return min(requested, configured)


def _request_headers(api_key: str, *, content_type: str | None = None) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def _request_json(
    method: str,
    url: str,
    headers: dict[str, str],
    body: Any | None,
    timeout: float,
) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload: Any = json.loads(raw)
        except json.JSONDecodeError:
            payload = raw
        return exc.code, payload
    except (TimeoutError, socket.timeout):
        return 0, {"error": {"message": f"request timed out after {timeout:g}s"}}
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        detail = (
            f"request timed out after {timeout:g}s"
            if isinstance(reason, (TimeoutError, socket.timeout))
            else str(reason or exc)
        )
        return 0, {"error": {"message": detail}}
    except json.JSONDecodeError:
        return 0, {"error": {"message": "endpoint returned invalid JSON"}}


def _format_error(status: int, payload: Any, base_url: str) -> str:
    detail = ""
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            detail = error["message"].strip()
        elif isinstance(error, str):
            detail = error.strip()
    elif isinstance(payload, str):
        detail = payload.strip()
    state = f"HTTP {status}" if status else "connection failed"
    suffix = f": {detail}" if detail else ""
    return f"OpenAI-compatible endpoint {base_url} {state}{suffix}"
