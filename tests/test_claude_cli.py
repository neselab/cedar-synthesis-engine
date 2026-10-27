from __future__ import annotations

import json
import os
import stat
import subprocess
from typing import Any

import pytest
from pydantic import BaseModel

from autocedar.providers.base import ChatMessage, InstructionPart
from autocedar.providers.claude_cli import ClaudeCLIBackend, ClaudeCLIError


class Answer(BaseModel):
    answer: str


class RecordingRunner:
    def __init__(self, payload: dict[str, Any], *, returncode: int = 0) -> None:
        self.payload = payload
        self.returncode = returncode
        self.calls: list[dict[str, Any]] = []

    def __call__(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cwd = kwargs.get("cwd")
        mode = stat.S_IMODE(os.stat(cwd).st_mode) if cwd else None
        self.calls.append({"command": command, "cwd_mode": mode, **kwargs})
        return subprocess.CompletedProcess(
            command,
            self.returncode,
            stdout=json.dumps(self.payload),
            stderr="provider failed" if self.returncode else "",
        )


def test_claude_cli_isolates_model_call_and_sends_prompt_only_on_stdin() -> None:
    runner = RecordingRunner({
        "type": "result",
        "subtype": "success",
        "result": "answer",
        "session_id": "session-1",
        "usage": {
            "input_tokens": 11,
            "output_tokens": 2,
            "cache_read_input_tokens": 5,
        },
    })
    backend = ClaudeCLIBackend(
        executable="/usr/local/bin/claude",
        runner=runner,
        environ={
            "PATH": "/usr/bin",
            "ANTHROPIC_API_KEY": "must-not-leak",
            "AWS_ACCESS_KEY_ID": "must-not-leak",
            "CLAUDE_CODE_USE_BEDROCK": "1",
        },
    )

    result = backend.generate_text(
        model="sonnet",
        system=(InstructionPart("system"),),
        messages=(ChatMessage(role="user", content="private prompt"),),
        reasoning_effort="max",
    )

    assert result.text == "answer"
    assert result.usage.cache_read_input_tokens == 5
    call = runner.calls[0]
    command = call["command"]
    assert "--bare" not in command
    assert command[:2] == ["/usr/local/bin/claude", "--print"]
    assert command[command.index("--max-turns") + 1] == "1"
    assert command[command.index("--effort") + 1] == "max"
    assert command[command.index("--tools") + 1] == ""
    assert "--disable-slash-commands" in command
    assert "--strict-mcp-config" in command
    assert "--no-session-persistence" in command
    assert "private prompt" not in " ".join(command)
    assert "private prompt" in call["input"]
    assert call["cwd_mode"] == 0o700
    assert call["shell"] is False
    assert "ANTHROPIC_API_KEY" not in call["env"]
    assert "AWS_ACCESS_KEY_ID" not in call["env"]
    assert "CLAUDE_CODE_USE_BEDROCK" not in call["env"]


def test_claude_cli_structured_output_is_validated() -> None:
    runner = RecordingRunner({
        "type": "result",
        "subtype": "success",
        "structured_output": {"answer": "yes"},
        "usage": {"input_tokens": 3, "output_tokens": 2},
    })
    backend = ClaudeCLIBackend(executable="claude", runner=runner, environ={})

    result = backend.generate_structured(
        model="sonnet",
        messages=(ChatMessage(role="user", content="question"),),
        output_type=Answer,
    )

    assert result.parsed == Answer(answer="yes")
    command = runner.calls[0]["command"]
    assert "--json-schema" in command
    # Turns beyond the first two let the CLI ask the model to fix an answer
    # that fails the schema.
    assert command[command.index("--max-turns") + 1] == "5"


OUT_OF_TURNS = {"type": "result", "subtype": "error_max_turns", "terminal_reason": "max_turns", "is_error": True}


def test_claude_cli_out_of_turns_is_retried_once_then_named() -> None:
    runner = RecordingRunner(OUT_OF_TURNS, returncode=1)
    backend = ClaudeCLIBackend(executable="claude", runner=runner, environ={})

    with pytest.raises(ClaudeCLIError, match=r"error_max_turns \(max_turns\)"):
        backend.generate_structured(
            model="sonnet",
            messages=(ChatMessage(role="user", content="question"),),
            output_type=Answer,
        )
    assert len(runner.calls) == 3


def test_claude_cli_retries_when_its_own_schema_fixes_run_out() -> None:
    gave_up = RecordingRunner(
        {"type": "result", "subtype": "error_max_structured_output_retries",
         "terminal_reason": "structured_output_retry_exhausted", "is_error": True},
        returncode=1,
    )
    answered = RecordingRunner({"type": "result", "subtype": "success", "structured_output": {"answer": "yes"}})
    runners = iter([gave_up, answered])
    backend = ClaudeCLIBackend(
        executable="claude",
        runner=lambda command, **kwargs: next(runners)(command, **kwargs),
        environ={},
    )

    result = backend.generate_structured(
        model="sonnet",
        messages=(ChatMessage(role="user", content="question"),),
        output_type=Answer,
    )

    assert result.parsed == Answer(answer="yes")


def test_claude_cli_out_of_turns_retry_can_succeed() -> None:
    first = RecordingRunner(OUT_OF_TURNS, returncode=1)
    second = RecordingRunner({"type": "result", "subtype": "success", "structured_output": {"answer": "yes"}})
    runners = iter([first, second])
    backend = ClaudeCLIBackend(
        executable="claude",
        runner=lambda command, **kwargs: next(runners)(command, **kwargs),
        environ={},
    )

    result = backend.generate_structured(
        model="sonnet",
        messages=(ChatMessage(role="user", content="question"),),
        output_type=Answer,
    )

    assert result.parsed == Answer(answer="yes")
    assert len(first.calls) == len(second.calls) == 1


def test_claude_cli_failure_is_bounded_and_does_not_echo_prompt() -> None:
    runner = RecordingRunner({}, returncode=2)
    backend = ClaudeCLIBackend(executable="claude", runner=runner, environ={})

    with pytest.raises(ClaudeCLIError, match="provider failed") as caught:
        backend.generate_text(
            model="sonnet",
            messages=(ChatMessage(role="user", content="top secret prompt"),),
        )

    assert "top secret prompt" not in str(caught.value)


def test_claude_cli_auth_status_uses_machine_readable_command() -> None:
    runner = RecordingRunner({
        "loggedIn": True,
        "authMethod": "claude.ai",
        "apiProvider": "firstParty",
        "subscriptionType": "max",
    })
    backend = ClaudeCLIBackend(executable="claude", runner=runner, environ={})

    status = backend.auth_status()

    assert status.logged_in is True
    assert status.auth_method == "claude.ai"
    assert status.subscription_type == "max"
    assert runner.calls[0]["command"] == ["claude", "auth", "status", "--json"]


def test_claude_cli_schema_drops_openapi_discriminators_only() -> None:
    from typing import Annotated, Literal, Union

    from pydantic import Field

    class Cat(BaseModel):
        kind: Literal["cat"]
        discriminator: str = ""

    class Dog(BaseModel):
        kind: Literal["dog"]

    class Pets(BaseModel):
        pets: list[Annotated[Union[Cat, Dog], Field(discriminator="kind")]]

    assert '"propertyName"' in json.dumps(Pets.model_json_schema())
    runner = RecordingRunner({"type": "result", "subtype": "success", "structured_output": {"pets": []}})
    backend = ClaudeCLIBackend(executable="claude", runner=runner, environ={})

    backend.generate_structured(
        model="sonnet",
        messages=(ChatMessage(role="user", content="question"),),
        output_type=Pets,
    )

    command = runner.calls[0]["command"]
    schema = command[command.index("--json-schema") + 1]
    assert "propertyName" not in schema
    assert '"oneOf"' in schema
    # A field that happens to be named "discriminator" stays in the schema.
    assert '"discriminator":{' in schema
