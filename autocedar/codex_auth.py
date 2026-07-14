"""OpenAI Codex OAuth bridge for AutoCedar.

This adapter uses the same broad pattern Hermes uses for its ``openai-codex``
provider: resolve a ChatGPT/Codex OAuth access token, call the Codex Responses
backend directly, and discover visible model slugs from the token-backed models
endpoint.  Token bytes are never rendered in user-facing output.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import stat
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from pydantic import BaseModel


DEFAULT_CODEX_MODEL = "gpt-5.5"
DEFAULT_CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
CODEX_OAUTH_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CODEX_OAUTH_TOKEN_URL = "https://auth.openai.com/oauth/token"
CODEX_PROVIDERS = {"codex", "openai", "openai-codex"}
CODEX_REASONING_EFFORTS = ("low", "medium", "high")
AUTOCEDAR_EFFORTS = ("low", "medium", "high", "max")
_REFRESH_SKEW_SECONDS = 120

_JSONRequester = Callable[[str, str, dict[str, str], Any | None, float], tuple[int, Any]]


class CodexAuthError(RuntimeError):
    """Raised when local Codex OAuth credentials are unavailable or invalid."""


@dataclass(frozen=True)
class CodexCredentials:
    access_token: str
    refresh_token: str | None
    source: str
    auth_path: Path | None
    base_url: str = DEFAULT_CODEX_BASE_URL


@dataclass(frozen=True)
class CodexRuntimeInfo:
    provider: str
    model: str
    base_url: str
    auth_source: str
    auth_available: bool
    models: list[str]
    thinking_efforts: tuple[str, ...] = AUTOCEDAR_EFFORTS
    model_details: list["CodexModelInfo"] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class CodexModelInfo:
    slug: str
    display_name: str = ""
    description: str = ""
    default_reasoning_level: str = ""
    supported_reasoning_levels: tuple[tuple[str, str], ...] = ()
    context_window: int | None = None
    max_context_window: int | None = None
    service_tiers: tuple[str, ...] = ()
    speed_tiers: tuple[str, ...] = ()
    default_verbosity: str = ""
    support_verbosity: bool = False
    supports_reasoning_summaries: bool = False

    @property
    def public_efforts(self) -> tuple[str, ...]:
        efforts = [effort for effort, _ in self.supported_reasoning_levels]
        return tuple(_public_effort_name(effort) for effort in efforts)


def is_codex_provider(provider: str | None) -> bool:
    return (provider or "").strip().lower() in CODEX_PROVIDERS


def codex_reasoning_effort(effort: str | None) -> str:
    normalized = (effort or "high").strip().lower()
    if normalized == "max":
        return "xhigh"
    if normalized in {*CODEX_REASONING_EFFORTS, "xhigh"}:
        return normalized
    return "high"


def codex_base_url() -> str:
    return (
        os.environ.get("AUTOCEDAR_CODEX_BASE_URL", "").strip().rstrip("/")
        or DEFAULT_CODEX_BASE_URL
    )


def codex_auth_path() -> Path:
    explicit = os.environ.get("AUTOCEDAR_CODEX_AUTH_PATH", "").strip()
    if explicit:
        return Path(explicit).expanduser()
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if not codex_home:
        codex_home = str(Path.home() / ".codex")
    return Path(codex_home).expanduser() / "auth.json"


def codex_auth_available() -> bool:
    """Cheap local readiness check that never refreshes or validates remotely."""

    if os.environ.get("AUTOCEDAR_CODEX_ACCESS_TOKEN", "").strip():
        return True
    try:
        payload = _read_auth_payload(codex_auth_path())
    except CodexAuthError:
        return False
    tokens = payload.get("tokens")
    return isinstance(tokens, dict) and bool(_clean_token(tokens.get("access_token")))


def resolve_codex_credentials(
    *,
    force_refresh: bool = False,
    requester: _JSONRequester | None = None,
) -> CodexCredentials:
    """Resolve a usable Codex access token from env or the Codex auth file."""

    env_token = os.environ.get("AUTOCEDAR_CODEX_ACCESS_TOKEN", "").strip()
    if env_token:
        return CodexCredentials(
            access_token=env_token,
            refresh_token=None,
            source="AUTOCEDAR_CODEX_ACCESS_TOKEN",
            auth_path=None,
            base_url=codex_base_url(),
        )

    auth_path = codex_auth_path()
    payload = _read_auth_payload(auth_path)
    tokens = payload.get("tokens")
    if not isinstance(tokens, dict):
        raise CodexAuthError(
            f"Codex auth file has no tokens object: {auth_path}. Run `codex login` first.",
        )
    access_token = _clean_token(tokens.get("access_token"))
    refresh_token = _clean_token(tokens.get("refresh_token"))
    if not access_token:
        raise CodexAuthError(
            f"Codex auth file is missing access_token: {auth_path}. Run `codex login` again.",
        )
    if force_refresh or _access_token_is_expiring(access_token, _REFRESH_SKEW_SECONDS):
        if not refresh_token:
            raise CodexAuthError(
                f"Codex access token is expiring but no refresh_token exists in {auth_path}. "
                "Run `codex login` again.",
            )
        updated = refresh_codex_tokens(
            dict(tokens),
            requester=requester,
        )
        payload["tokens"] = updated
        _write_auth_payload(auth_path, payload)
        access_token = _clean_token(updated.get("access_token"))
        refresh_token = _clean_token(updated.get("refresh_token"))
        if not access_token:
            raise CodexAuthError("Codex token refresh did not return an access token.")

    return CodexCredentials(
        access_token=access_token,
        refresh_token=refresh_token,
        source=str(auth_path),
        auth_path=auth_path,
        base_url=codex_base_url(),
    )


def refresh_codex_tokens(
    tokens: dict[str, Any],
    *,
    requester: _JSONRequester | None = None,
    timeout: float = 20.0,
) -> dict[str, str]:
    refresh_token = _clean_token(tokens.get("refresh_token"))
    if not refresh_token:
        raise CodexAuthError("Cannot refresh Codex auth without refresh_token.")

    requester = requester or _request_json
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CODEX_OAUTH_CLIENT_ID,
    })
    status, payload = requester(
        "POST",
        CODEX_OAUTH_TOKEN_URL,
        {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body,
        timeout,
    )
    if status != 200 or not isinstance(payload, dict):
        message = "Codex token refresh failed"
        if isinstance(payload, dict):
            detail = payload.get("error_description") or payload.get("message") or payload.get("error")
            if isinstance(detail, str) and detail.strip():
                message = f"{message}: {detail.strip()}"
        raise CodexAuthError(message)
    access_token = _clean_token(payload.get("access_token"))
    if not access_token:
        raise CodexAuthError("Codex token refresh response was missing access_token.")
    updated: dict[str, str] = {
        key: str(value)
        for key, value in tokens.items()
        if isinstance(value, str)
    }
    updated["access_token"] = access_token
    new_refresh = _clean_token(payload.get("refresh_token"))
    if new_refresh:
        updated["refresh_token"] = new_refresh
    return updated


def list_codex_models(
    *,
    credentials: CodexCredentials | None = None,
    requester: _JSONRequester | None = None,
    timeout: float = 10.0,
) -> list[str]:
    """Return model slugs visible to the active Codex OAuth token."""

    credentials = credentials or resolve_codex_credentials(requester=requester)
    requester = requester or _request_json
    url = f"{credentials.base_url.rstrip('/')}/models?client_version=1.0.0"
    status, payload = requester(
        "GET",
        url,
        _codex_request_headers(credentials),
        None,
        timeout,
    )
    if status != 200 or not isinstance(payload, dict):
        raise CodexAuthError(f"Codex model discovery failed with status {status}.")
    entries = payload.get("models")
    if not isinstance(entries, list):
        return [DEFAULT_CODEX_MODEL]

    model_details = _model_details_from_payload(payload)
    models = [detail.slug for detail in model_details]
    if DEFAULT_CODEX_MODEL not in models:
        models.insert(0, DEFAULT_CODEX_MODEL)
    return models or [DEFAULT_CODEX_MODEL]


def list_codex_model_details(
    *,
    credentials: CodexCredentials | None = None,
    requester: _JSONRequester | None = None,
    timeout: float = 10.0,
) -> list[CodexModelInfo]:
    """Return visible Codex model metadata for the active OAuth token."""

    credentials = credentials or resolve_codex_credentials(requester=requester)
    requester = requester or _request_json
    url = f"{credentials.base_url.rstrip('/')}/models?client_version=1.0.0"
    status, payload = requester(
        "GET",
        url,
        _codex_request_headers(credentials),
        None,
        timeout,
    )
    if status != 200 or not isinstance(payload, dict):
        raise CodexAuthError(f"Codex model discovery failed with status {status}.")
    details = _model_details_from_payload(payload)
    if DEFAULT_CODEX_MODEL not in {detail.slug for detail in details}:
        details.insert(0, CodexModelInfo(slug=DEFAULT_CODEX_MODEL))
    return details or [CodexModelInfo(slug=DEFAULT_CODEX_MODEL)]


def _model_details_from_payload(payload: dict[str, Any]) -> list[CodexModelInfo]:
    entries = payload.get("models")
    if not isinstance(entries, list):
        return []

    sortable: list[tuple[int, CodexModelInfo]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        slug = item.get("slug")
        if not isinstance(slug, str) or not slug.strip():
            continue
        if item.get("supported_in_api") is False:
            continue
        visibility = item.get("visibility")
        if isinstance(visibility, str) and visibility.strip().lower() in {"hide", "hidden"}:
            continue
        priority = item.get("priority")
        rank = int(priority) if isinstance(priority, (int, float)) else 10_000
        sortable.append((rank, _model_info_from_entry(item, slug.strip())))

    sortable.sort(key=lambda pair: (pair[0], pair[1].slug))
    details: list[CodexModelInfo] = []
    seen: set[str] = set()
    for _, detail in sortable:
        if detail.slug not in seen:
            details.append(detail)
            seen.add(detail.slug)
    return details


def _model_info_from_entry(item: dict[str, Any], slug: str) -> CodexModelInfo:
    supported_reasoning: list[tuple[str, str]] = []
    levels = item.get("supported_reasoning_levels")
    if isinstance(levels, list):
        for level in levels:
            if not isinstance(level, dict):
                continue
            effort = level.get("effort")
            if not isinstance(effort, str) or not effort.strip():
                continue
            description = level.get("description")
            supported_reasoning.append((
                effort.strip(),
                description.strip() if isinstance(description, str) else "",
            ))
    return CodexModelInfo(
        slug=slug,
        display_name=_str_field(item.get("display_name")),
        description=_str_field(item.get("description")),
        default_reasoning_level=_str_field(item.get("default_reasoning_level")),
        supported_reasoning_levels=tuple(supported_reasoning),
        context_window=_int_field(item.get("context_window")),
        max_context_window=_int_field(item.get("max_context_window")),
        service_tiers=tuple(_service_tier_names(item.get("service_tiers"))),
        speed_tiers=tuple(_str_list(item.get("additional_speed_tiers"))),
        default_verbosity=_str_field(item.get("default_verbosity")),
        support_verbosity=bool(item.get("support_verbosity")),
        supports_reasoning_summaries=bool(item.get("supports_reasoning_summaries")),
    )


def codex_runtime_info(*, requester: _JSONRequester | None = None) -> CodexRuntimeInfo:
    try:
        credentials = resolve_codex_credentials(requester=requester)
        model_details = list_codex_model_details(credentials=credentials, requester=requester)
        models = [detail.slug for detail in model_details]
        efforts = _runtime_efforts_from_models(model_details)
        return CodexRuntimeInfo(
            provider="openai-codex",
            model=models[0] if models else DEFAULT_CODEX_MODEL,
            base_url=credentials.base_url,
            auth_source=credentials.source,
            auth_available=True,
            models=models,
            thinking_efforts=efforts,
            model_details=model_details,
        )
    except Exception as exc:
        return CodexRuntimeInfo(
            provider="openai-codex",
            model=DEFAULT_CODEX_MODEL,
            base_url=codex_base_url(),
            auth_source=str(codex_auth_path()),
            auth_available=False,
            models=[DEFAULT_CODEX_MODEL],
            model_details=[CodexModelInfo(slug=DEFAULT_CODEX_MODEL)],
            error=str(exc),
        )


class CodexAuthClient:
    """Anthropic-message-shaped client backed by the Codex Responses endpoint."""

    def __init__(
        self,
        *,
        credentials: CodexCredentials | None = None,
        requester: _JSONRequester | None = None,
        timeout: float = 240.0,
    ) -> None:
        self._requester = requester or _request_json
        self._credentials = credentials
        self._timeout = _configured_timeout(timeout)
        self.messages = _CodexMessages(self)

    def _credentials_for_call(self) -> CodexCredentials:
        if self._credentials is not None:
            return self._credentials
        self._credentials = resolve_codex_credentials(requester=self._requester)
        return self._credentials


def _configured_timeout(default: float) -> float:
    raw = os.environ.get("AUTOCEDAR_CODEX_TIMEOUT_SECONDS")
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return max(value, 1.0)


class _CodexMessages:
    def __init__(self, parent: CodexAuthClient) -> None:
        self._parent = parent

    def parse(self, **kwargs: Any) -> Any:
        output_format = kwargs.get("output_format")
        if not isinstance(output_format, type) or not issubclass(output_format, BaseModel):
            raise TypeError("CodexAuthClient.parse requires a Pydantic output_format")

        schema_json = json.dumps(_codex_strict_schema(output_format.model_json_schema()), indent=2)
        user_messages = list(kwargs.get("messages") or [])
        user_messages.append({
            "role": "user",
            "content": (
                "Return only a JSON object matching this JSON Schema. Do not wrap it "
                "in Markdown and do not include explanatory prose.\n\n"
                f"```json\n{schema_json}\n```"
            ),
        })
        text, usage = self._run_response_with_usage(dict(kwargs, messages=user_messages))
        payload = _loads_json_object(text)
        return SimpleNamespace(
            parsed_output=output_format.model_validate(payload),
            usage=usage,
        )

    def create(self, **kwargs: Any) -> Any:
        text, usage = self._run_response_with_usage(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=text)],
            usage=usage,
        )

    def _run_response(self, kwargs: dict[str, Any]) -> str:
        text, _ = self._run_response_with_usage(kwargs)
        return text

    def _run_response_with_usage(self, kwargs: dict[str, Any]) -> tuple[str, Any]:
        credentials = self._parent._credentials_for_call()
        model = str(kwargs.get("model") or DEFAULT_CODEX_MODEL)
        effort = codex_reasoning_effort(_extract_effort(kwargs))
        payload = {
            "model": model,
            "instructions": _render_content(kwargs.get("system")),
            "input": _messages_to_responses_input(kwargs.get("messages")),
            "store": False,
            "stream": True,
            "reasoning": {"effort": effort, "summary": "auto"},
            "include": ["reasoning.encrypted_content"],
        }
        status, response = self._parent._requester(
            "POST",
            f"{credentials.base_url.rstrip('/')}/responses",
            _codex_request_headers(credentials, content_type="application/json"),
            payload,
            self._parent._timeout,
        )
        if status in {401, 403}:
            self._parent._credentials = resolve_codex_credentials(
                force_refresh=True,
                requester=self._parent._requester,
            )
            credentials = self._parent._credentials
            status, response = self._parent._requester(
                "POST",
                f"{credentials.base_url.rstrip('/')}/responses",
                _codex_request_headers(credentials, content_type="application/json"),
                payload,
                self._parent._timeout,
            )
        if (
            status != 200
            or not isinstance(response, dict)
            or response.get("error") is not None
        ):
            raise CodexAuthError(_format_codex_response_error(status, response))
        try:
            return _extract_response_text(response), _extract_response_usage(response)
        except CodexAuthError as exc:
            if "no text output" not in str(exc):
                raise
            status, response = self._parent._requester(
                "POST",
                f"{credentials.base_url.rstrip('/')}/responses",
                _codex_request_headers(credentials, content_type="application/json"),
                payload,
                self._parent._timeout,
            )
            if (
                status != 200
                or not isinstance(response, dict)
                or response.get("error") is not None
            ):
                raise CodexAuthError(_format_codex_response_error(status, response)) from exc
            return _extract_response_text(response), _extract_response_usage(response)


def _request_json(
    method: str,
    url: str,
    headers: dict[str, str],
    body: Any | None,
    timeout: float,
) -> tuple[int, Any]:
    data: bytes | None
    if body is None:
        data = None
    elif isinstance(body, str):
        data = body.encode("utf-8")
    else:
        data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )
    expects_stream = isinstance(body, dict) and body.get("stream") is True
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = _read_response_body(response, timeout=timeout, expects_stream=expects_stream)
            return response.status, _decode_response_body(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload: Any = _decode_response_body(raw)
        except json.JSONDecodeError:
            payload = raw
        return exc.code, payload
    except (TimeoutError, socket.timeout):
        return 0, {
            "error": {
                "type": "timeout",
                "message": f"request timed out after {timeout:g}s",
            },
        }
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            detail = f"request timed out after {timeout:g}s"
        else:
            detail = str(reason or exc)
        return 0, {
            "error": {
                "type": "transport_error",
                "message": detail,
            },
        }


def _read_response_body(response: Any, *, timeout: float, expects_stream: bool = False) -> str:
    """Read a normal response or SSE stream with an overall timeout.

    The Codex backend currently requires ``stream: true`` for Responses calls.
    AutoCedar's structured-output adapter still needs a single final payload,
    so stop reading once the terminal SSE event arrives instead of blocking on a
    full ``response.read()`` that may wait for the socket to close.
    """

    content_type = ""
    headers = getattr(response, "headers", None)
    if headers is not None:
        getter = getattr(headers, "get", None)
        if callable(getter):
            content_type = str(getter("Content-Type", "") or "").lower()
    if not expects_stream and "text/event-stream" not in content_type:
        return response.read().decode("utf-8")

    deadline = time.monotonic() + max(timeout, 0.1)
    raw_blocks: list[str] = []
    block_lines: list[str] = []
    while True:
        if time.monotonic() > deadline:
            raise TimeoutError(f"request timed out after {timeout:g}s")
        line_bytes = response.readline()
        if not line_bytes:
            if block_lines:
                raw_blocks.append("\n".join(block_lines))
            break
        line = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
        if line:
            block_lines.append(line)
            continue
        if not block_lines:
            continue
        block = "\n".join(block_lines)
        raw_blocks.append(block)
        block_lines = []
        if _sse_block_is_terminal(block):
            break
    return "\n\n".join(raw_blocks)


def _decode_response_body(raw: str) -> Any:
    if not raw:
        return {
            "error": {
                "type": "empty_response",
                "message": "Codex Responses API returned an empty response body.",
            },
        }
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        sse_payload = _decode_sse_response(raw)
        if sse_payload is not None:
            return sse_payload
        return {
            "error": {
                "type": "invalid_json_response",
                "message": "Codex Responses API returned a non-JSON response body.",
                "body_preview": raw[:500],
            },
        }


def _decode_sse_response(raw: str) -> Any | None:
    terminal: Any | None = None
    text_parts: list[str] = []
    for block in raw.split("\n\n"):
        event_type = ""
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data_lines.append(line.split(":", 1)[1].strip())
        if not data_lines:
            continue
        data = "\n".join(data_lines)
        if data == "[DONE]":
            continue
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            continue
        payload_type = payload.get("type") if isinstance(payload, dict) else None
        resolved_type = event_type or str(payload_type or "")
        if resolved_type == "response.output_text.delta" and isinstance(payload, dict):
            delta = payload.get("delta")
            if isinstance(delta, str):
                text_parts.append(delta)
            continue
        if resolved_type in {"response.completed", "response.failed", "response.incomplete"}:
            if isinstance(payload, dict) and isinstance(payload.get("response"), dict):
                terminal = payload["response"]
            else:
                terminal = payload
    if isinstance(terminal, dict) and text_parts and not terminal.get("output_text"):
        terminal = dict(terminal)
        terminal["output_text"] = "".join(text_parts)
    return terminal


def _sse_block_is_terminal(block: str) -> bool:
    event_type = ""
    payload_type = ""
    for line in block.splitlines():
        if line.startswith("event:"):
            event_type = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data = line.split(":", 1)[1].strip()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                raw_type = payload.get("type")
                if isinstance(raw_type, str):
                    payload_type = raw_type
    resolved = event_type or payload_type
    return resolved in {"response.completed", "response.failed", "response.incomplete"}


def _read_auth_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CodexAuthError(f"Codex auth file not found: {path}. Run `codex login` first.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CodexAuthError(f"Could not read Codex auth file: {path}") from exc
    if not isinstance(payload, dict):
        raise CodexAuthError(f"Codex auth file is not a JSON object: {path}")
    return payload


def _write_auth_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp.{os.getpid()}.{int(time.time() * 1000)}")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def _clean_token(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _str_field(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _int_field(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def _service_tier_names(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    names: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            names.append(item.strip())
        elif isinstance(item, dict):
            label = item.get("name") or item.get("id")
            if isinstance(label, str) and label.strip():
                names.append(label.strip())
    return names


def _codex_request_headers(
    credentials: CodexCredentials,
    *,
    content_type: str | None = None,
) -> dict[str, str]:
    """Headers expected by the ChatGPT Codex backend.

    Hermes mirrors the upstream codex-rs client here because the backend can
    route or challenge requests differently based on the originator headers.
    The account id is embedded in Codex OAuth JWTs and is optional for malformed
    or env-supplied tokens.
    """

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {credentials.access_token}",
        "User-Agent": "codex_cli_rs/0.0.0 (AutoCedar)",
        "originator": "codex_cli_rs",
    }
    account_id = _codex_account_id(credentials.access_token)
    if account_id:
        headers["ChatGPT-Account-ID"] = account_id
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def _codex_account_id(token: str) -> str:
    claims = _decode_jwt_claims(token)
    auth_claim = claims.get("https://api.openai.com/auth")
    if not isinstance(auth_claim, dict):
        return ""
    account_id = auth_claim.get("chatgpt_account_id")
    return account_id.strip() if isinstance(account_id, str) else ""


def _public_effort_name(effort: str) -> str:
    normalized = effort.strip().lower()
    return "max" if normalized == "xhigh" else normalized


def _runtime_efforts_from_models(details: list[CodexModelInfo]) -> tuple[str, ...]:
    ordered: list[str] = []
    for detail in details:
        for effort in detail.public_efforts:
            if effort and effort not in ordered:
                ordered.append(effort)
    return tuple(ordered) or AUTOCEDAR_EFFORTS


def _decode_jwt_claims(token: str) -> dict[str, Any]:
    if token.count(".") != 2:
        return {}
    payload = token.split(".")[1]
    payload += "=" * ((4 - len(payload) % 4) % 4)
    try:
        raw = base64.urlsafe_b64decode(payload.encode("utf-8"))
        decoded = json.loads(raw.decode("utf-8"))
    except Exception:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _access_token_is_expiring(token: str, skew_seconds: int) -> bool:
    exp = _decode_jwt_claims(token).get("exp")
    if not isinstance(exp, (int, float)):
        return False
    return float(exp) <= (time.time() + max(0, skew_seconds))


def _extract_effort(kwargs: dict[str, Any]) -> str | None:
    output_config = kwargs.get("output_config")
    if isinstance(output_config, dict):
        effort = output_config.get("effort")
        if isinstance(effort, str):
            return effort
    return None


def _codex_strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    copied = json.loads(json.dumps(schema))
    _add_no_extra_properties(copied)
    return copied


def _add_no_extra_properties(node: Any) -> None:
    if isinstance(node, dict):
        if "oneOf" in node:
            node["anyOf"] = node.pop("oneOf")
            node.pop("discriminator", None)
        if node.get("type") == "object" or "properties" in node:
            node["additionalProperties"] = False
            properties = node.get("properties")
            if isinstance(properties, dict):
                node["required"] = list(properties)
        for value in node.values():
            _add_no_extra_properties(value)
    elif isinstance(node, list):
        for item in node:
            _add_no_extra_properties(item)


def _render_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)
        return "\n\n".join(parts)
    return str(content or "")


def _messages_to_responses_input(messages: Any) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    if not isinstance(messages, list):
        return output
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "user")
        if role == "system":
            role = "developer"
        content = _render_content(message.get("content"))
        output.append({
            "role": role,
            "content": content,
        })
    return output


def _extract_response_text(response: dict[str, Any]) -> str:
    output = response.get("output")
    parts: list[str] = []
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") in {"output_text", "text"} and isinstance(block.get("text"), str):
                    parts.append(block["text"])
    if not parts and isinstance(response.get("output_text"), str):
        parts.append(response["output_text"])
    text = "\n".join(part for part in parts if part).strip()
    if not text:
        raise CodexAuthError("Codex Responses API returned no text output.")
    return text


def _extract_response_usage(response: dict[str, Any]) -> Any:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        return SimpleNamespace(input_tokens=0, output_tokens=0)

    def _int_token(*keys: str) -> int:
        for key in keys:
            value = usage.get(key)
            if isinstance(value, bool):
                continue
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
        return 0

    return SimpleNamespace(
        input_tokens=_int_token("input_tokens", "prompt_tokens"),
        output_tokens=_int_token("output_tokens", "completion_tokens"),
    )


def _format_codex_response_error(status: int, response: Any) -> str:
    message = f"Codex Responses API failed with status {status}."
    if isinstance(response, dict):
        error = response.get("error")
        if isinstance(error, dict):
            detail = error.get("message") or error.get("code") or error.get("type")
            if isinstance(detail, str) and detail.strip():
                return f"{message} {detail.strip()}"
        detail = response.get("message")
        if isinstance(detail, str) and detail.strip():
            return f"{message} {detail.strip()}"
        try:
            rendered = json.dumps(response, sort_keys=True)[:500]
        except TypeError:
            rendered = str(response)[:500]
        if rendered and rendered != "{}":
            return f"{message} {rendered}"
    elif isinstance(response, str) and response.strip():
        return f"{message} {response.strip()[:500]}"
    return message


def _loads_json_object(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        if start == -1:
            raise
        payload, _ = json.JSONDecoder().raw_decode(text[start:])
        return payload
