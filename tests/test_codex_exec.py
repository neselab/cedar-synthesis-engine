from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from autocedar.codex_exec import CodexExecClient, _codex_strict_schema, codex_reasoning_effort


class _Answer(BaseModel):
    answer: str


def _write_last_message(cmd: list[str], text: str) -> None:
    out_path = Path(cmd[cmd.index("--output-last-message") + 1])
    out_path.write_text(text, encoding="utf-8")


def test_codex_reasoning_effort_maps_autocedar_max_to_xhigh() -> None:
    assert codex_reasoning_effort("max") == "xhigh"
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


def test_codex_parse_uses_output_schema_and_validates_json(tmp_path: Path) -> None:
    seen: dict[str, Any] = {}

    def runner(cmd: list[str], prompt: str | None, cwd: Path) -> subprocess.CompletedProcess[str]:
        seen["cmd"] = cmd
        seen["prompt"] = prompt
        seen["cwd"] = cwd
        schema_path = Path(cmd[cmd.index("--output-schema") + 1])
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        assert schema["title"] == "_Answer"
        assert schema["additionalProperties"] is False
        assert schema["required"] == ["answer"]
        _write_last_message(cmd, '{"answer":"OK"}')
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    client = CodexExecClient(cwd=tmp_path, runner=runner)
    response = client.messages.parse(
        model="gpt-test",
        output_config={"effort": "max"},
        system=[{"type": "text", "text": "system prompt"}],
        messages=[{"role": "user", "content": "user turn"}],
        output_format=_Answer,
    )

    assert response.parsed_output == _Answer(answer="OK")
    cmd = seen["cmd"]
    assert cmd[:2] == ["codex", "exec"]
    assert "--ignore-user-config" in cmd
    assert "--ignore-rules" in cmd
    assert "--ephemeral" in cmd
    assert ["-m", "gpt-test"] == cmd[cmd.index("-m") : cmd.index("-m") + 2]
    assert 'model_reasoning_effort="xhigh"' in cmd
    assert seen["cwd"] == tmp_path
    assert "system prompt" in seen["prompt"]
    assert "user turn" in seen["prompt"]


def test_codex_create_returns_text_block(tmp_path: Path) -> None:
    def runner(cmd: list[str], prompt: str | None, cwd: Path) -> subprocess.CompletedProcess[str]:
        assert "--output-schema" not in cmd
        _write_last_message(cmd, "plain answer")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    client = CodexExecClient(cwd=tmp_path, runner=runner)
    response = client.messages.create(
        model="gpt-test",
        output_config={"effort": "low"},
        system="system prompt",
        messages=[{"role": "user", "content": "hello"}],
    )

    assert response.content[0].type == "text"
    assert response.content[0].text == "plain answer"


def test_codex_parse_falls_back_when_cli_rejects_schema(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def runner(cmd: list[str], prompt: str | None, cwd: Path) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        if len(calls) == 1:
            return subprocess.CompletedProcess(
                cmd,
                1,
                stdout="",
                stderr='{"code":"invalid_json_schema"}',
            )
        assert "--output-schema" not in cmd
        assert "The output schema is:" in (prompt or "")
        _write_last_message(cmd, '```json\n{"answer":"OK"}\n```')
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    client = CodexExecClient(cwd=tmp_path, runner=runner)
    response = client.messages.parse(
        model="gpt-test",
        output_config={"effort": "low"},
        system="system prompt",
        messages=[{"role": "user", "content": "hello"}],
        output_format=_Answer,
    )

    assert len(calls) == 2
    assert "--output-schema" in calls[0]
    assert response.parsed_output == _Answer(answer="OK")
