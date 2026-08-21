"""Check a local OpenAI-compatible server and exercise two tiny requests.

This is a backend plumbing check only.  It does not validate Cedar policies or
replace the manual semantic review required by AutoCedar's HITL workflow.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Callable


DEFAULT_BASE_URL = "http://127.0.0.1:8000/v1"
DEFAULT_MODEL = "autocedar-local"
DEFAULT_TIMEOUT_SECONDS = 600.0

_JSONRequester = Callable[
    [str, dict[str, str], dict[str, Any], float],
    tuple[int, Any],
]
_JSONGetter = Callable[[str, dict[str, str], float], tuple[int, Any]]


class SmokeError(RuntimeError):
    """Raised when the local model fails a plumbing smoke check."""


@dataclass(frozen=True)
class SmokeResult:
    """Validated outputs from the two plumbing requests."""

    text: str
    structured: dict[str, str]


def check_model_ready(
    *,
    base_url: str,
    api_key: str,
    model: str,
    timeout: float = 3.0,
    getter: _JSONGetter | None = None,
) -> list[str]:
    """Require the expected model name at an OpenAI-compatible endpoint."""

    resolved_base_url = base_url.strip().rstrip("/")
    expected = model.strip()
    if not resolved_base_url:
        raise ValueError("base_url must not be empty")
    if not expected:
        raise ValueError("model must not be empty")
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")

    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    status, response = (getter or _get_json)(
        f"{resolved_base_url}/models",
        headers,
        timeout,
    )
    if status != 200:
        raise SmokeError(f"model-list request failed with HTTP {status}")
    if not isinstance(response, dict) or not isinstance(response.get("data"), list):
        raise SmokeError("model-list request returned an invalid response")
    models = [
        item["id"]
        for item in response["data"]
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    ]
    if expected not in models:
        available = ", ".join(models) if models else "none"
        raise SmokeError(
            f"expected model {expected!r} is not advertised; available: {available}",
        )
    return models


def run_smoke(
    *,
    base_url: str,
    api_key: str,
    model: str,
    timeout: float,
    requester: _JSONRequester | None = None,
) -> SmokeResult:
    """Run plain-text and JSON-schema completion plumbing checks."""

    resolved_base_url = base_url.strip().rstrip("/")
    if not resolved_base_url:
        raise ValueError("base_url must not be empty")
    if not model.strip():
        raise ValueError("model must not be empty")
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")

    request_json = requester or _request_json
    url = f"{resolved_base_url}/chat/completions"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    text_payload: dict[str, Any] = {
        "model": model.strip(),
        "messages": [
            {
                "role": "user",
                "content": "Reply with a short confirmation that the model is ready.",
            },
        ],
        "stream": False,
        "max_tokens": 64,
        "temperature": 0,
    }
    text_status, text_response = request_json(
        url,
        headers,
        text_payload,
        timeout,
    )
    text = _completion_text(text_status, text_response, check_name="ordinary chat")

    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "const": "ok"},
        },
        "required": ["status"],
        "additionalProperties": False,
    }
    structured_payload: dict[str, Any] = {
        "model": model.strip(),
        "messages": [
            {
                "role": "user",
                "content": 'Return a JSON object whose status field is exactly "ok".',
            },
        ],
        "stream": False,
        "max_tokens": 64,
        "temperature": 0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "autocedar_jarvis_smoke",
                "schema": schema,
            },
        },
    }
    structured_status, structured_response = request_json(
        url,
        headers,
        structured_payload,
        timeout,
    )
    structured_text = _completion_text(
        structured_status,
        structured_response,
        check_name="JSON-schema chat",
    )
    try:
        structured = json.loads(structured_text)
    except json.JSONDecodeError as exc:
        raise SmokeError("JSON-schema chat returned invalid JSON") from exc
    if structured != {"status": "ok"}:
        raise SmokeError(
            'JSON-schema chat did not return exactly {"status": "ok"}',
        )

    return SmokeResult(text=text, structured=structured)


def _completion_text(status: int, response: Any, *, check_name: str) -> str:
    if status != 200:
        raise SmokeError(f"{check_name} request failed with HTTP {status}")
    if not isinstance(response, dict):
        raise SmokeError(f"{check_name} returned a non-object response")
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise SmokeError(f"{check_name} returned no choices")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise SmokeError(f"{check_name} returned no message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise SmokeError(f"{check_name} returned empty text")
    return content.strip()


def _request_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: float,
) -> tuple[int, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        return exc.code, _decode_error_body(exc.read())
    except (TimeoutError, socket.timeout):
        raise SmokeError(f"request timed out after {timeout:g} seconds") from None
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            raise SmokeError(f"request timed out after {timeout:g} seconds") from None
        raise SmokeError(f"could not reach the local model server: {reason or exc}") from None
    except json.JSONDecodeError:
        raise SmokeError("local model server returned invalid response JSON") from None


def _get_json(
    url: str,
    headers: dict[str, str],
    timeout: float,
) -> tuple[int, Any]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        return exc.code, _decode_error_body(exc.read())
    except (TimeoutError, socket.timeout):
        raise SmokeError(f"request timed out after {timeout:g} seconds") from None
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            raise SmokeError(f"request timed out after {timeout:g} seconds") from None
        raise SmokeError(f"could not reach the local model server: {reason or exc}") from None
    except json.JSONDecodeError:
        raise SmokeError("local model server returned invalid response JSON") from None


def _decode_error_body(raw: bytes) -> Any:
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text) if text else {}
    except json.JSONDecodeError:
        return text


def _environment_timeout() -> float:
    raw = os.environ.get("AUTOCEDAR_LOCAL_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        timeout = float(raw)
    except ValueError as exc:
        raise ValueError("AUTOCEDAR_LOCAL_TIMEOUT_SECONDS must be a number") from exc
    if timeout <= 0:
        raise ValueError("AUTOCEDAR_LOCAL_TIMEOUT_SECONDS must be greater than zero")
    return timeout


def main(argv: Sequence[str] = ()) -> None:
    """Read endpoint settings from the environment and run the requested check."""

    readiness_check = list(argv) == ["--readiness-check"]
    if argv and not readiness_check:
        raise SystemExit("usage: model_smoke.py [--readiness-check]")

    base_url = os.environ.get("AUTOCEDAR_LOCAL_BASE_URL", DEFAULT_BASE_URL)
    api_key = os.environ.get("AUTOCEDAR_LOCAL_API_KEY", "")
    model = os.environ.get("AUTOCEDAR_LOCAL_MODEL", DEFAULT_MODEL)
    if readiness_check:
        try:
            check_model_ready(
                base_url=base_url,
                api_key=api_key,
                model=model,
            )
        except (SmokeError, ValueError) as exc:
            raise SystemExit(f"Local model is not ready: {exc}") from None
        return

    try:
        run_smoke(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout=_environment_timeout(),
        )
    except (SmokeError, ValueError) as exc:
        raise SystemExit(f"Local-model plumbing smoke test failed: {exc}") from None

    print("Ordinary chat completion: OK")
    print("JSON-schema chat completion: OK")
    print("Backend plumbing passed; Cedar semantics still require human review.")


if __name__ == "__main__":
    main(sys.argv[1:])
