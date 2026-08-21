from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "autocedar-jarvis" / "scripts" / "model_smoke.py"
SPEC = importlib.util.spec_from_file_location("jarvis_model_smoke", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
model_smoke = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = model_smoke
SPEC.loader.exec_module(model_smoke)


def test_run_smoke_sends_plain_and_json_schema_requests() -> None:
    calls: list[dict[str, Any]] = []

    def requester(url, headers, payload, timeout):
        calls.append(
            {
                "url": url,
                "headers": headers,
                "payload": payload,
                "timeout": timeout,
            },
        )
        content = "model ready" if len(calls) == 1 else '{"status":"ok"}'
        return 200, {"choices": [{"message": {"content": content}}]}

    result = model_smoke.run_smoke(
        base_url="http://gpu-node:8000/v1/",
        api_key="local-secret",
        model="autocedar-local",
        timeout=45,
        requester=requester,
    )

    assert result.text == "model ready"
    assert result.structured == {"status": "ok"}
    assert len(calls) == 2
    assert all(call["url"] == "http://gpu-node:8000/v1/chat/completions" for call in calls)
    assert all(call["headers"]["Authorization"] == "Bearer local-secret" for call in calls)
    assert all(call["timeout"] == 45 for call in calls)

    plain = calls[0]["payload"]
    structured = calls[1]["payload"]
    assert plain["model"] == "autocedar-local"
    assert plain["stream"] is False
    assert "response_format" not in plain
    assert structured["response_format"]["type"] == "json_schema"
    schema = structured["response_format"]["json_schema"]["schema"]
    assert schema["properties"]["status"] == {"type": "string", "const": "ok"}
    assert schema["required"] == ["status"]
    assert schema["additionalProperties"] is False


def test_check_model_ready_requires_expected_advertised_name() -> None:
    def getter(url, headers, timeout):
        assert url == "http://gpu-node:8123/v1/models"
        assert headers["Authorization"] == "Bearer local-secret"
        assert timeout == 2
        return 200, {"data": [{"id": "autocedar-local"}]}

    models = model_smoke.check_model_ready(
        base_url="http://gpu-node:8123/v1/",
        api_key="local-secret",
        model="autocedar-local",
        timeout=2,
        getter=getter,
    )

    assert models == ["autocedar-local"]


def test_check_model_ready_rejects_another_users_server() -> None:
    def getter(*args):
        return 200, {"data": [{"id": "/home/other-user/qwen3-8b"}]}

    with pytest.raises(model_smoke.SmokeError, match="expected model.*not advertised"):
        model_smoke.check_model_ready(
            base_url="http://127.0.0.1:8000/v1",
            api_key="job-secret",
            model="autocedar-local",
            getter=getter,
        )


def test_run_smoke_rejects_empty_plain_text_before_structured_request() -> None:
    calls = 0

    def requester(*args):
        nonlocal calls
        calls += 1
        return 200, {"choices": [{"message": {"content": "  "}}]}

    with pytest.raises(model_smoke.SmokeError, match="ordinary chat returned empty text"):
        model_smoke.run_smoke(
            base_url="http://node:8000/v1",
            api_key="",
            model="model",
            timeout=10,
            requester=requester,
        )

    assert calls == 1


@pytest.mark.parametrize(
    ("content", "error"),
    [
        ("not json", "returned invalid JSON"),
        ('{"status":"wrong"}', "did not return exactly"),
        ('{"status":"ok","extra":true}', "did not return exactly"),
    ],
)
def test_run_smoke_validates_exact_structured_result(content: str, error: str) -> None:
    responses = iter(("ready", content))

    def requester(*args):
        return 200, {"choices": [{"message": {"content": next(responses)}}]}

    with pytest.raises(model_smoke.SmokeError, match=error):
        model_smoke.run_smoke(
            base_url="http://node:8000/v1",
            api_key="",
            model="model",
            timeout=10,
            requester=requester,
        )


def test_main_reads_local_model_environment(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen: dict[str, Any] = {}

    def fake_run_smoke(**kwargs):
        seen.update(kwargs)
        return model_smoke.SmokeResult(text="ready", structured={"status": "ok"})

    monkeypatch.setenv("AUTOCEDAR_LOCAL_BASE_URL", "http://node:9000/v1")
    monkeypatch.setenv("AUTOCEDAR_LOCAL_API_KEY", "env-key")
    monkeypatch.setenv("AUTOCEDAR_LOCAL_MODEL", "env-model")
    monkeypatch.setenv("AUTOCEDAR_LOCAL_TIMEOUT_SECONDS", "123")
    monkeypatch.setattr(model_smoke, "run_smoke", fake_run_smoke)

    model_smoke.main()

    assert seen == {
        "base_url": "http://node:9000/v1",
        "api_key": "env-key",
        "model": "env-model",
        "timeout": 123.0,
    }
    output = capsys.readouterr().out
    assert "Backend plumbing passed" in output
    assert "Cedar semantics still require human review" in output


def test_readiness_main_uses_local_model_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, Any] = {}

    def fake_check_model_ready(**kwargs):
        seen.update(kwargs)
        return ["env-model"]

    monkeypatch.setenv("AUTOCEDAR_LOCAL_BASE_URL", "http://node:9123/v1")
    monkeypatch.setenv("AUTOCEDAR_LOCAL_API_KEY", "env-key")
    monkeypatch.setenv("AUTOCEDAR_LOCAL_MODEL", "env-model")
    monkeypatch.setattr(model_smoke, "check_model_ready", fake_check_model_ready)

    model_smoke.main(["--readiness-check"])

    assert seen == {
        "base_url": "http://node:9123/v1",
        "api_key": "env-key",
        "model": "env-model",
    }
