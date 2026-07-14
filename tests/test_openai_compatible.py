from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from autocedar.openai_compatible import (
    DEFAULT_OPENAI_BASE_URL,
    DEFAULT_OPENAI_MODEL,
    OpenAICompatibleClient,
    OpenAICompatibleError,
    is_openai_compatible_provider,
    list_openai_models,
    openai_base_url,
    openai_model,
    openai_runtime_info,
)
from autocedar.providers.base import ChatMessage, InstructionPart


class Answer(BaseModel):
    answer: str


def test_openai_compatible_configuration_and_aliases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for provider in ("openai-compatible", "local", "vllm"):
        assert is_openai_compatible_provider(provider)
    assert not is_openai_compatible_provider("codex")
    assert not is_openai_compatible_provider("openai")

    monkeypatch.delenv("AUTOCEDAR_OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_OPENAI_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_LOCAL_BASE_URL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_LOCAL_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_AUTHOR_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_CHAT_MODEL", raising=False)
    assert openai_base_url() == DEFAULT_OPENAI_BASE_URL
    assert openai_model() == DEFAULT_OPENAI_MODEL

    monkeypatch.setenv("AUTOCEDAR_LOCAL_BASE_URL", "http://gpu-node:9000/v1/")
    monkeypatch.setenv("AUTOCEDAR_LOCAL_MODEL", "served-model")
    assert openai_base_url() == "http://gpu-node:9000/v1"
    assert openai_model() == "served-model"


def test_list_models_uses_optional_bearer_key() -> None:
    seen: dict[str, Any] = {}

    def requester(method, url, headers, body, timeout):
        seen.update(method=method, url=url, headers=headers, body=body, timeout=timeout)
        return 200, {"data": [{"id": "model-a"}, {"id": "model-b"}]}

    models = list_openai_models(
        base_url="http://node:8000/v1",
        api_key="local-key",
        requester=requester,
    )

    assert models == ["model-a", "model-b"]
    assert seen["method"] == "GET"
    assert seen["url"] == "http://node:8000/v1/models"
    assert seen["headers"]["Authorization"] == "Bearer local-key"
    assert seen["body"] is None


def test_direct_openai_environment_names_do_not_configure_local_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AUTOCEDAR_LOCAL_BASE_URL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_LOCAL_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_AUTHOR_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_CHAT_MODEL", raising=False)
    monkeypatch.setenv("AUTOCEDAR_OPENAI_BASE_URL", "http://legacy:8000/v1")
    monkeypatch.setenv("AUTOCEDAR_OPENAI_MODEL", "legacy-model")

    assert openai_base_url() == DEFAULT_OPENAI_BASE_URL
    assert openai_model() == DEFAULT_OPENAI_MODEL


def test_list_models_rejects_reachable_server_with_no_models() -> None:
    with pytest.raises(OpenAICompatibleError, match="advertises no usable models"):
        list_openai_models(
            requester=lambda *args: (200, {"data": []}),
        )


def test_runtime_info_reports_reachable_and_unreachable_endpoints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_LOCAL_BASE_URL", "http://node:8000/v1")
    monkeypatch.setenv("AUTOCEDAR_LOCAL_MODEL", "model-a")

    ready = openai_runtime_info(
        requester=lambda *args: (200, {"data": [{"id": "model-a"}]}),
    )
    assert ready.available is True
    assert ready.models == ["model-a"]

    missing = openai_runtime_info(
        requester=lambda *args: (0, {"error": {"message": "connection refused"}}),
    )
    assert missing.available is False
    assert "connection refused" in (missing.error or "")


def test_create_translates_current_autocedar_request_shape() -> None:
    seen: dict[str, Any] = {}

    def requester(method, url, headers, body, timeout):
        seen.update(method=method, url=url, headers=headers, body=body, timeout=timeout)
        return 200, {
            "choices": [{"message": {"role": "assistant", "content": "permit (...);"}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 4},
        }

    client = OpenAICompatibleClient(
        base_url="http://node:8000/v1",
        api_key="local-key",
        requester=requester,
    )
    response = client.messages.create(
        model="autocedar-local",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=[
            {"type": "text", "text": "system prompt"},
            {
                "type": "text",
                "text": "<spec>requirements</spec>",
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[{"role": "user", "content": "write Cedar"}],
    )

    assert response.content[0].text == "permit (...);"
    assert response.usage.input_tokens == 12
    assert response.usage.output_tokens == 4
    assert seen["url"] == "http://node:8000/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer local-key"
    payload = seen["body"]
    assert payload["model"] == "autocedar-local"
    assert payload["max_tokens"] == 4096
    assert payload["stream"] is False
    assert payload["messages"] == [
        {
            "role": "system",
            "content": "system prompt\n\n<spec>requirements</spec>",
        },
        {"role": "user", "content": "write Cedar"},
    ]
    assert "thinking" not in payload
    assert "output_config" not in payload
    assert "cache_control" not in str(payload)


def test_local_max_tokens_caps_only_compatible_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, Any] = {}

    def requester(method, url, headers, body, timeout):
        seen["body"] = body
        return 200, {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setenv("AUTOCEDAR_LOCAL_MAX_TOKENS", "4096")
    OpenAICompatibleClient(requester=requester).messages.create(
        model="autocedar-local",
        max_tokens=16000,
        messages=[{"role": "user", "content": "hello"}],
    )

    assert seen["body"]["max_tokens"] == 4096


def test_parse_uses_json_schema_and_validates_locally() -> None:
    seen: dict[str, Any] = {}

    def requester(method, url, headers, body, timeout):
        seen["body"] = body
        return 200, {
            "choices": [{"message": {"content": '{"answer":"yes"}'}}],
            "usage": {"prompt_tokens": 8, "completion_tokens": 3},
        }

    client = OpenAICompatibleClient(requester=requester)
    response = client.messages.parse(
        model="autocedar-local",
        max_tokens=100,
        system="system",
        messages=[{"role": "user", "content": "question"}],
        output_format=Answer,
    )

    assert response.parsed_output == Answer(answer="yes")
    assert response.usage.input_tokens == 8
    assert seen["body"]["response_format"]["type"] == "json_schema"
    assert seen["body"]["response_format"]["json_schema"]["schema"]["type"] == "object"
    assert "JSON Schema" in seen["body"]["messages"][-1]["content"]


def test_parse_retries_prompt_only_when_server_rejects_response_format() -> None:
    payloads: list[dict[str, Any]] = []

    def requester(method, url, headers, body, timeout):
        payloads.append(body)
        if len(payloads) == 1:
            return 400, {"error": {"message": "response_format json_schema unsupported"}}
        return 200, {"choices": [{"message": {"content": "```json\n{\"answer\":\"ok\"}\n```"}}]}

    response = OpenAICompatibleClient(requester=requester).messages.parse(
        model="autocedar-local",
        system="system",
        messages=[{"role": "user", "content": "question"}],
        output_format=Answer,
    )

    assert response.parsed_output.answer == "ok"
    assert "response_format" in payloads[0]
    assert "response_format" not in payloads[1]


def test_parse_rejects_invalid_local_model_json() -> None:
    client = OpenAICompatibleClient(
        requester=lambda *args: (
            200,
            {"choices": [{"message": {"content": "not json"}}]},
        ),
    )

    with pytest.raises(OpenAICompatibleError, match="invalid Answer JSON"):
        client.messages.parse(
            model="autocedar-local",
            system="system",
            messages=[{"role": "user", "content": "question"}],
            output_format=Answer,
        )


def test_create_surfaces_endpoint_error() -> None:
    client = OpenAICompatibleClient(
        base_url="http://node:8000/v1",
        requester=lambda *args: (503, {"error": {"message": "model still loading"}}),
    )

    with pytest.raises(OpenAICompatibleError, match="HTTP 503: model still loading"):
        client.messages.create(
            model="autocedar-local",
            system="system",
            messages=[{"role": "user", "content": "hello"}],
        )


def test_local_native_backend_method_does_not_require_messages_shape() -> None:
    seen: dict[str, Any] = {}

    def requester(method, url, headers, body, timeout):
        seen["body"] = body
        return 200, {
            "id": "chat_native",
            "model": "local-native",
            "choices": [{"message": {"content": "native"}}],
            "usage": {
                "prompt_tokens": 7,
                "completion_tokens": 2,
                "prompt_tokens_details": {"cached_tokens": 3},
            },
        }

    client = OpenAICompatibleClient(requester=requester)
    result = client.generate_text(
        model="local-native",
        system=(InstructionPart("one"), InstructionPart("two")),
        messages=(ChatMessage(role="user", content="hello"),),
        max_tokens=99,
    )

    assert result.text == "native"
    assert result.usage.cache_read_input_tokens == 3
    assert result.request_id == "chat_native"
    assert seen["body"]["messages"] == [
        {"role": "system", "content": "one\n\ntwo"},
        {"role": "user", "content": "hello"},
    ]
