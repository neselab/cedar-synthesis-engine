from __future__ import annotations

import base64
import json
import os
import stat
import tempfile
import time
from pathlib import Path
from typing import Any
import urllib.request

import pytest
from pydantic import BaseModel

from autocedar.codex_auth import (
    CODEX_OAUTH_TOKEN_URL,
    DEFAULT_CODEX_BASE_URL,
    DEFAULT_CODEX_MODEL,
    CodexAuthError,
    CodexAuthClient,
    CodexCredentials,
    _codex_strict_schema,
    _codex_request_headers,
    _decode_response_body,
    _decode_sse_response,
    _loads_json_object,
    _request_json,
    codex_auth_available,
    codex_reasoning_effort,
    list_codex_models,
    list_codex_model_details,
    resolve_codex_credentials,
)
from autocedar.providers.base import ChatMessage, InstructionPart

import autocedar.codex_auth as codex_auth


class _Answer(BaseModel):
    answer: str


def _jwt(exp: int) -> str:
    header = _b64({"alg": "none"})
    payload = _b64({"exp": exp})
    return f"{header}.{payload}.sig"


def _b64(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _codex_jwt(account_id: str = "acct-test") -> str:
    header = _b64({"alg": "none"})
    payload = _b64({
        "https://api.openai.com/auth": {
            "chatgpt_account_id": account_id,
        },
    })
    return f"{header}.{payload}.sig"


def test_codex_reasoning_effort_maps_autocedar_max_to_xhigh() -> None:
    assert codex_reasoning_effort("max") == "xhigh"
    assert codex_reasoning_effort("xhigh") == "xhigh"
    assert codex_reasoning_effort("high") == "high"
    assert codex_reasoning_effort("nonsense") == "high"


def test_codex_strict_schema_converts_pydantic_union_shape() -> None:
    schema = {
        "type": "object",
        "properties": {
            "item": {
                "oneOf": [{"type": "object", "properties": {"kind": {"const": "a"}}}],
                "discriminator": {"propertyName": "kind"},
            },
        },
    }

    strict = _codex_strict_schema(schema)

    assert "oneOf" not in strict["properties"]["item"]
    assert "discriminator" not in strict["properties"]["item"]
    assert "anyOf" in strict["properties"]["item"]
    assert strict["required"] == ["item"]


def test_codex_request_headers_match_codex_backend_shape() -> None:
    credentials = CodexCredentials(
        access_token=_codex_jwt("acct_123"),
        refresh_token="refresh",
        source="test",
        auth_path=None,
        base_url=DEFAULT_CODEX_BASE_URL,
    )

    headers = _codex_request_headers(credentials, content_type="application/json")

    assert headers["Authorization"].startswith("Bearer ")
    assert headers["User-Agent"].startswith("codex_cli_rs/0.0.0")
    assert headers["originator"] == "codex_cli_rs"
    assert headers["ChatGPT-Account-ID"] == "acct_123"
    assert headers["Content-Type"] == "application/json"


def test_resolve_codex_credentials_reads_codex_home_auth(
    monkeypatch,
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    auth_path = codex_home / "auth.json"
    auth_path.write_text(
        json.dumps({"tokens": {"access_token": "access", "refresh_token": "refresh"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    monkeypatch.delenv("AUTOCEDAR_CODEX_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("AUTOCEDAR_CODEX_AUTH_PATH", raising=False)

    assert codex_auth_available() is True
    credentials = resolve_codex_credentials()

    assert credentials.access_token == "access"
    assert credentials.refresh_token == "refresh"
    assert credentials.source == str(auth_path)


def test_resolve_codex_credentials_refreshes_expiring_token(
    monkeypatch,
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    auth_path = codex_home / "auth.json"
    auth_path.write_text(
        json.dumps({
            "tokens": {
                "access_token": _jwt(int(time.time()) - 10),
                "refresh_token": "old-refresh",
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    calls: list[tuple[str, str, Any]] = []

    def requester(method: str, url: str, headers: dict[str, str], body: Any, timeout: float):
        calls.append((method, url, body))
        assert url == CODEX_OAUTH_TOKEN_URL
        assert "refresh_token=old-refresh" in body
        return 200, {"access_token": "new-access", "refresh_token": "new-refresh"}

    credentials = resolve_codex_credentials(requester=requester)

    assert credentials.access_token == "new-access"
    assert credentials.refresh_token == "new-refresh"
    saved = json.loads(auth_path.read_text(encoding="utf-8"))
    assert saved["tokens"]["access_token"] == "new-access"
    assert saved["tokens"]["refresh_token"] == "new-refresh"
    assert calls


def test_codex_auth_token_write_is_private_durable_and_atomic(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    auth_path = tmp_path / "codex" / "auth.json"
    real_mkstemp = tempfile.mkstemp
    real_fsync = os.fsync
    real_replace = os.replace
    observed: dict[str, object] = {"events": []}

    def tracking_mkstemp(*args, **kwargs):
        fd, name = real_mkstemp(*args, **kwargs)
        observed["created_mode"] = stat.S_IMODE(os.fstat(fd).st_mode)
        return fd, name

    def tracking_fsync(fd: int) -> None:
        observed["events"].append("fsync")  # type: ignore[union-attr]
        real_fsync(fd)

    def tracking_replace(source, destination) -> None:
        observed["replace_source"] = Path(source)
        observed["replace_destination"] = Path(destination)
        observed["replace_mode"] = stat.S_IMODE(Path(source).stat().st_mode)
        observed["events"].append("replace")  # type: ignore[union-attr]
        real_replace(source, destination)

    monkeypatch.setattr(codex_auth.tempfile, "mkstemp", tracking_mkstemp)
    monkeypatch.setattr(codex_auth.os, "fsync", tracking_fsync)
    monkeypatch.setattr(codex_auth.os, "replace", tracking_replace)

    previous_umask = os.umask(0)
    try:
        codex_auth._write_auth_payload(
            auth_path,
            {"tokens": {"access_token": "new-access", "refresh_token": "new-refresh"}},
        )
    finally:
        os.umask(previous_umask)

    events = observed["events"]
    assert observed["created_mode"] == 0o600
    assert observed["replace_mode"] == 0o600
    assert observed["replace_destination"] == auth_path
    assert events.index("fsync") < events.index("replace")  # type: ignore[union-attr]
    assert stat.S_IMODE(auth_path.stat().st_mode) == 0o600
    assert not observed["replace_source"].exists()  # type: ignore[union-attr]


def test_list_codex_models_filters_and_sorts_visible_api_models() -> None:
    credentials = CodexCredentials(
        access_token=_codex_jwt("acct_models"),
        refresh_token="refresh",
        source="test",
        auth_path=None,
        base_url=DEFAULT_CODEX_BASE_URL,
    )

    def requester(method: str, url: str, headers: dict[str, str], body: Any, timeout: float):
        assert method == "GET"
        assert url.endswith("/models?client_version=1.0.0")
        assert headers["Authorization"] == f"Bearer {credentials.access_token}"
        assert headers["originator"] == "codex_cli_rs"
        assert headers["ChatGPT-Account-ID"] == "acct_models"
        return 200, {
            "models": [
                {"slug": "hidden", "visibility": "hidden", "priority": 1},
                {"slug": "unsupported", "supported_in_api": False, "priority": 2},
                {"slug": "gpt-later", "priority": 20},
                {
                    "slug": "gpt-first",
                    "priority": 3,
                    "supported_reasoning_levels": [
                        {"effort": "low", "description": "fast"},
                        {"effort": "xhigh", "description": "deep"},
                    ],
                    "default_reasoning_level": "medium",
                    "additional_speed_tiers": ["fast"],
                    "service_tiers": [{"name": "Fast"}],
                    "context_window": 123,
                    "max_context_window": 456,
                    "default_verbosity": "low",
                    "support_verbosity": True,
                    "supports_reasoning_summaries": True,
                },
            ],
        }

    assert list_codex_models(credentials=credentials, requester=requester) == [
        DEFAULT_CODEX_MODEL,
        "gpt-first",
        "gpt-later",
    ]
    details = list_codex_model_details(credentials=credentials, requester=requester)
    first = next(detail for detail in details if detail.slug == "gpt-first")
    assert first.public_efforts == ("low", "max")
    assert first.default_reasoning_level == "medium"
    assert first.speed_tiers == ("fast",)
    assert first.service_tiers == ("Fast",)
    assert first.context_window == 123
    assert first.max_context_window == 456
    assert first.default_verbosity == "low"
    assert first.support_verbosity is True
    assert first.supports_reasoning_summaries is True


def test_codex_parse_uses_responses_payload_and_validates_json() -> None:
    credentials = CodexCredentials(
        access_token=_codex_jwt("acct_parse"),
        refresh_token="refresh",
        source="test",
        auth_path=None,
        base_url=DEFAULT_CODEX_BASE_URL,
    )
    seen: dict[str, Any] = {}

    def requester(method: str, url: str, headers: dict[str, str], body: Any, timeout: float):
        seen["method"] = method
        seen["url"] = url
        seen["headers"] = headers
        seen["body"] = body
        return 200, {
            "usage": {"input_tokens": 12, "output_tokens": 3},
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": '{"answer":"OK"}'}],
                },
            ],
        }

    client = CodexAuthClient(credentials=credentials, requester=requester)
    response = client.messages.parse(
        model="gpt-test",
        output_config={"effort": "max"},
        system=[{"type": "text", "text": "system prompt"}],
        messages=[{"role": "user", "content": "user turn"}],
        output_format=_Answer,
    )

    assert response.parsed_output == _Answer(answer="OK")
    assert response.usage.input_tokens == 12
    assert response.usage.output_tokens == 3
    assert seen["method"] == "POST"
    assert seen["url"].endswith("/responses")
    assert seen["headers"]["Authorization"] == f"Bearer {credentials.access_token}"
    assert seen["headers"]["originator"] == "codex_cli_rs"
    assert seen["headers"]["ChatGPT-Account-ID"] == "acct_parse"
    body = seen["body"]
    assert body["model"] == "gpt-test"
    assert body["instructions"] == "system prompt"
    assert body["stream"] is True
    assert body["reasoning"] == {"effort": "xhigh", "summary": "auto"}
    assert body["include"] == ["reasoning.encrypted_content"]
    assert "JSON Schema" in body["input"][-1]["content"]


def test_loads_json_object_accepts_trailing_response_fragments() -> None:
    assert _loads_json_object('{"answer":"OK"}\n{"extra": true}') == {"answer": "OK"}
    assert _loads_json_object('prefix\n{"answer":"OK"}\ntrailing text') == {
        "answer": "OK",
    }


def test_codex_parse_retries_once_after_empty_text_output() -> None:
    credentials = CodexCredentials(
        access_token=_codex_jwt("acct_parse"),
        refresh_token="refresh",
        source="test",
        auth_path=None,
        base_url=DEFAULT_CODEX_BASE_URL,
    )
    calls = 0

    def requester(method: str, url: str, headers: dict[str, str], body: Any, timeout: float):
        nonlocal calls
        _ = method, url, headers, body, timeout
        calls += 1
        if calls == 1:
            return 200, {
                "usage": {"input_tokens": 12, "output_tokens": 0},
                "output": [],
            }
        return 200, {
            "usage": {"input_tokens": 12, "output_tokens": 3},
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": '{"answer":"OK"}'}],
                },
            ],
        }

    client = CodexAuthClient(credentials=credentials, requester=requester)
    response = client.messages.parse(
        model="gpt-test",
        system=[{"type": "text", "text": "system prompt"}],
        messages=[{"role": "user", "content": "user turn"}],
        output_format=_Answer,
    )

    assert calls == 2
    assert response.parsed_output == _Answer(answer="OK")


def test_codex_parse_accepts_success_payload_with_null_error() -> None:
    credentials = CodexCredentials(
        access_token=_codex_jwt("acct_parse"),
        refresh_token="refresh",
        source="test",
        auth_path=None,
        base_url=DEFAULT_CODEX_BASE_URL,
    )

    def requester(method: str, url: str, headers: dict[str, str], body: Any, timeout: float):
        _ = method, url, headers, body, timeout
        return 200, {
            "error": None,
            "usage": {"input_tokens": 12, "output_tokens": 3},
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": '{"answer":"OK"}'}],
                },
            ],
        }

    client = CodexAuthClient(credentials=credentials, requester=requester)
    response = client.messages.parse(
        model="gpt-test",
        system=[{"type": "text", "text": "system prompt"}],
        messages=[{"role": "user", "content": "user turn"}],
        output_format=_Answer,
    )

    assert response.parsed_output == _Answer(answer="OK")


def test_codex_parse_raises_clear_error_for_error_payload_with_200_status() -> None:
    credentials = CodexCredentials(
        access_token=_codex_jwt("acct_parse"),
        refresh_token="refresh",
        source="test",
        auth_path=None,
        base_url=DEFAULT_CODEX_BASE_URL,
    )

    def requester(method: str, url: str, headers: dict[str, str], body: Any, timeout: float):
        _ = method, url, headers, body, timeout
        return 200, {
            "error": {
                "type": "invalid_json_response",
                "message": "Codex Responses API returned a non-JSON response body.",
                "body_preview": "<html>gateway timeout</html>",
            },
        }

    client = CodexAuthClient(credentials=credentials, requester=requester)
    with pytest.raises(CodexAuthError, match="non-JSON response body"):
        client.messages.parse(
            model="gpt-test",
            system=[{"type": "text", "text": "system prompt"}],
            messages=[{"role": "user", "content": "user turn"}],
            output_format=_Answer,
        )


def test_codex_create_refreshes_once_after_unauthorized(
    monkeypatch,
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    auth_path = codex_home / "auth.json"
    auth_path.write_text(
        json.dumps({"tokens": {"access_token": "old-access", "refresh_token": "refresh"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    calls: list[str] = []

    def requester(method: str, url: str, headers: dict[str, str], body: Any, timeout: float):
        calls.append(url)
        if url == CODEX_OAUTH_TOKEN_URL:
            return 200, {"access_token": "new-access", "refresh_token": "new-refresh"}
        if headers["Authorization"] == "Bearer old-access":
            return 401, {"error": {"message": "expired"}}
        assert headers["Authorization"] == "Bearer new-access"
        return 200, {
            "usage": {"input_tokens": 7, "output_tokens": 2},
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": "plain answer"}],
                },
            ],
        }

    client = CodexAuthClient(requester=requester)
    response = client.messages.create(
        model="gpt-test",
        output_config={"effort": "low"},
        system="system prompt",
        messages=[{"role": "user", "content": "hello"}],
    )

    assert response.content[0].text == "plain answer"
    assert response.usage.input_tokens == 7
    assert response.usage.output_tokens == 2
    assert calls.count(CODEX_OAUTH_TOKEN_URL) == 1


def test_decode_sse_response_accumulates_output_text_deltas() -> None:
    raw = "\n\n".join([
        'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","delta":"auto"}',
        'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","delta":"cedar"}',
        'event: response.completed\ndata: {"type":"response.completed","response":{"status":"completed","output":[]}}',
    ])

    assert _decode_sse_response(raw)["output_text"] == "autocedar"


def test_decode_response_body_classifies_empty_and_non_json_bodies() -> None:
    empty = _decode_response_body("")
    assert empty["error"]["type"] == "empty_response"

    html = _decode_response_body("<html>gateway timeout</html>")
    assert html["error"]["type"] == "invalid_json_response"
    assert "gateway timeout" in html["error"]["body_preview"]


def test_request_json_timeout_returns_structured_transport_error(
    monkeypatch,
) -> None:
    def timeout_urlopen(request: urllib.request.Request, timeout: float):
        _ = request, timeout
        raise TimeoutError("timed out")

    monkeypatch.setattr(urllib.request, "urlopen", timeout_urlopen)

    status, payload = _request_json(
        "POST",
        "https://example.test/responses",
        {"Content-Type": "application/json"},
        {"hello": "world"},
        3.0,
    )

    assert status == 0
    assert payload["error"]["type"] == "timeout"
    assert "3s" in payload["error"]["message"]


def test_request_json_reads_sse_until_terminal_event(
    monkeypatch,
) -> None:
    raw_lines = [
        b'event: response.output_text.delta\n',
        b'data: {"type":"response.output_text.delta","delta":"auto"}\n',
        b'\n',
        b'event: response.output_text.delta\n',
        b'data: {"type":"response.output_text.delta","delta":"cedar"}\n',
        b'\n',
        b'event: response.completed\n',
        b'data: {"type":"response.completed","response":{"status":"completed","output":[]}}\n',
        b'\n',
        b'event: should.not.be.read\n',
        b'data: {"type":"should.not.be.read"}\n',
        b'\n',
    ]

    class FakeResponse:
        status = 200
        headers = {"Content-Type": "application/json"}

        def __init__(self) -> None:
            self._lines = list(raw_lines)

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            _ = exc_type, exc, tb

        def readline(self) -> bytes:
            return self._lines.pop(0)

    def fake_urlopen(request: urllib.request.Request, timeout: float):
        _ = request, timeout
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    status, payload = _request_json(
        "POST",
        "https://example.test/responses",
        {"Content-Type": "application/json"},
        {"hello": "world", "stream": True},
        3.0,
    )

    assert status == 200
    assert payload["output_text"] == "autocedar"


def test_codex_native_backend_method_does_not_require_messages_shape() -> None:
    credentials = CodexCredentials(
        access_token=_codex_jwt("acct_native"),
        refresh_token="refresh",
        source="test",
        auth_path=None,
        base_url=DEFAULT_CODEX_BASE_URL,
    )
    seen: dict[str, Any] = {}

    def requester(method: str, url: str, headers: dict[str, str], body: Any, timeout: float):
        seen["body"] = body
        return 200, {
            "id": "resp_native",
            "model": "gpt-native",
            "usage": {
                "input_tokens": 6,
                "output_tokens": 2,
                "input_tokens_details": {"cached_tokens": 4},
            },
            "output": [{
                "type": "message",
                "content": [{"type": "output_text", "text": "native"}],
            }],
        }

    client = CodexAuthClient(credentials=credentials, requester=requester)
    result = client.generate_text(
        model="gpt-native",
        system=(InstructionPart("one"), InstructionPart("two")),
        messages=(ChatMessage(role="user", content="hello"),),
        reasoning_effort="max",
    )

    assert result.text == "native"
    assert result.usage.cache_read_input_tokens == 4
    assert result.request_id == "resp_native"
    assert seen["body"]["instructions"] == "one\n\ntwo"
    assert seen["body"]["input"] == [{"role": "user", "content": "hello"}]
