"""Hardened ``claude -p`` backend for subscription-authenticated Claude use."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence, TypeVar

from pydantic import BaseModel

from .base import (
    ChatMessage,
    InstructionPart,
    ModelBackend,
    ModelUsage,
    StructuredResult,
    TextResult,
)


DEFAULT_CLAUDE_CLI_MODEL = "sonnet"
DEFAULT_TIMEOUT_SECONDS = 600.0
_ERROR_PREVIEW_LIMIT = 800
_StructuredT = TypeVar("_StructuredT", bound=BaseModel)
_Runner = Callable[..., subprocess.CompletedProcess[str]]


class ClaudeCLIError(RuntimeError):
    """Raised when the isolated Claude CLI subprocess fails."""


@dataclass(frozen=True)
class ClaudeCLIAuthStatus:
    logged_in: bool
    auth_method: str = ""
    api_provider: str = ""
    subscription_type: str = ""
    error: str | None = None


class ClaudeCLIBackend(ModelBackend):
    """Run Claude CLI as a single-turn, tool-free model transport.

    OAuth/keychain authentication remains available, but AutoCedar does not
    expose its workspace or inherit Claude project configuration.  Every call
    runs in a new private, empty directory with prompts supplied over stdin.
    """

    provider_id = "claude-cli"

    def __init__(
        self,
        *,
        executable: str | None = None,
        runner: _Runner | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self.executable = executable or shutil.which("claude") or "claude"
        self._runner = runner or subprocess.run
        self.timeout = max(float(timeout), 1.0)
        self._environ = dict(environ) if environ is not None else None

    def auth_status(self) -> ClaudeCLIAuthStatus:
        """Return Claude CLI's subscription/keychain status without secrets."""

        try:
            completed = self._run(
                [self.executable, "auth", "status", "--json"],
                input_text=None,
                cwd=None,
                timeout=min(self.timeout, 30.0),
            )
            if completed.returncode != 0:
                return ClaudeCLIAuthStatus(
                    logged_in=False,
                    error=_bounded_process_error(completed),
                )
            payload = _json_payload(completed.stdout, context="Claude auth status")
            return ClaudeCLIAuthStatus(
                logged_in=payload.get("loggedIn") is True,
                auth_method=_string(payload.get("authMethod")),
                api_provider=_string(payload.get("apiProvider")),
                subscription_type=_string(payload.get("subscriptionType")),
            )
        except Exception as exc:
            return ClaudeCLIAuthStatus(
                logged_in=False,
                error=_bounded_text(str(exc)),
            )

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
        del max_tokens, temperature  # Claude CLI does not expose these controls.
        payload = self._generate(
            model=model,
            messages=messages,
            system=system,
            reasoning_effort=reasoning_effort,
            output_type=None,
        )
        result = payload.get("result")
        if not isinstance(result, str) or not result.strip():
            raise ClaudeCLIError("Claude CLI returned no text result.")
        return TextResult(
            text=result.strip(),
            usage=_claude_usage(payload.get("usage")),
            model=model,
            request_id=_optional_string(payload.get("session_id")),
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
        del max_tokens, temperature
        payload = self._generate(
            model=model,
            messages=messages,
            system=system,
            reasoning_effort=reasoning_effort,
            output_type=output_type,
        )
        value = payload.get("structured_output")
        if value is None:
            raw_result = payload.get("result")
            if isinstance(raw_result, str):
                try:
                    value = _extract_json_object(raw_result)
                except Exception as exc:
                    raise ClaudeCLIError(
                        f"Claude CLI returned invalid {output_type.__name__} JSON.",
                    ) from exc
        if value is None:
            raise ClaudeCLIError(
                f"Claude CLI returned no structured {output_type.__name__} result.",
            )
        try:
            parsed = value if isinstance(value, output_type) else output_type.model_validate(value)
        except Exception as exc:
            raise ClaudeCLIError(
                f"Claude CLI returned invalid {output_type.__name__} output: "
                f"{_bounded_text(str(exc))}",
            ) from exc
        return StructuredResult(
            parsed=parsed,
            usage=_claude_usage(payload.get("usage")),
            model=model,
            request_id=_optional_string(payload.get("session_id")),
        )

    def _generate(
        self,
        *,
        model: str,
        messages: Sequence[ChatMessage],
        system: str | Sequence[InstructionPart] | None,
        reasoning_effort: str | None,
        output_type: type[BaseModel] | None,
    ) -> dict[str, Any]:
        command = [
            self.executable,
            "--print",
            "--input-format",
            "text",
            "--output-format",
            "json",
            "--model",
            model or DEFAULT_CLAUDE_CLI_MODEL,
            "--max-turns",
            "1",
            "--tools",
            "",
            "--disable-slash-commands",
            "--strict-mcp-config",
            "--mcp-config",
            '{"mcpServers":{}}',
            "--setting-sources",
            "",
            "--settings",
            '{"enabledPlugins":{},"hooks":{}}',
            "--no-session-persistence",
            "--permission-mode",
            "dontAsk",
        ]
        if reasoning_effort:
            command.extend(["--effort", reasoning_effort])
        if output_type is not None:
            command.extend([
                "--json-schema",
                json.dumps(output_type.model_json_schema(), separators=(",", ":")),
            ])

        prompt = _render_prompt(messages=messages, system=system)
        try:
            with tempfile.TemporaryDirectory(prefix="autocedar-claude-") as temp_dir:
                private_cwd = Path(temp_dir)
                private_cwd.chmod(0o700)
                completed = self._run(
                    command,
                    input_text=prompt,
                    cwd=private_cwd,
                    timeout=self.timeout,
                )
        except subprocess.TimeoutExpired as exc:
            raise ClaudeCLIError(
                f"Claude CLI timed out after {self.timeout:g} seconds.",
            ) from exc
        except FileNotFoundError as exc:
            raise ClaudeCLIError(
                "Claude CLI is not installed or is not on PATH. Install it and run "
                "`claude auth status`.",
            ) from exc

        if completed.returncode != 0:
            raise ClaudeCLIError(_bounded_process_error(completed))
        payload = _json_payload(completed.stdout, context="Claude CLI")
        if payload.get("is_error") is True or payload.get("subtype") == "error":
            raise ClaudeCLIError(
                "Claude CLI reported an error: "
                + _bounded_text(_string(payload.get("result")) or "unknown error"),
            )
        return payload

    def _run(
        self,
        command: Sequence[str],
        *,
        input_text: str | None,
        cwd: Path | None,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        return self._runner(
            list(command),
            input=input_text,
            cwd=str(cwd) if cwd is not None else None,
            env=_sanitized_environment(self._environ),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )


def _render_prompt(
    *,
    messages: Sequence[ChatMessage],
    system: str | Sequence[InstructionPart] | None,
) -> str:
    if isinstance(system, str):
        system_text = system
    else:
        system_text = "\n\n".join(part.text for part in (system or ()))
    sections: list[str] = []
    if system_text.strip():
        sections.append(f"<system-instructions>\n{system_text}\n</system-instructions>")
    for message in messages:
        sections.append(f"<{message.role}>\n{message.content}\n</{message.role}>")
    if not sections:
        raise ClaudeCLIError("Claude CLI request contains no prompt content.")
    return "\n\n".join(sections) + "\n"


def _sanitized_environment(source: Mapping[str, str] | None) -> dict[str, str]:
    env = dict(source) if source is not None else dict(os.environ)
    exact = {
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY",
        "AWS_PROFILE",
        "AWS_DEFAULT_PROFILE",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "CLOUD_ML_REGION",
        "ANTHROPIC_VERTEX_PROJECT_ID",
        "ANTHROPIC_VERTEX_REGION",
    }
    for key in exact:
        env.pop(key, None)
    competing_prefixes = (
        "ANTHROPIC_",
        "AWS_",
        "GOOGLE_",
        "AZURE_",
        "CLAUDE_CODE_USE_",
    )
    for key in tuple(env):
        if key.startswith(competing_prefixes):
            env.pop(key, None)
    return env


def _claude_usage(value: Any) -> ModelUsage:
    return ModelUsage(
        input_tokens=_nonnegative_int(_field(value, "input_tokens")),
        output_tokens=_nonnegative_int(_field(value, "output_tokens")),
        cache_read_input_tokens=_nonnegative_int(
            _field(value, "cache_read_input_tokens"),
        ),
        cache_creation_input_tokens=_nonnegative_int(
            _field(value, "cache_creation_input_tokens"),
        ),
    )


def _json_payload(raw: str, *, context: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ClaudeCLIError(f"{context} returned invalid JSON output.") from exc
    if not isinstance(payload, dict):
        raise ClaudeCLIError(f"{context} returned a non-object JSON response.")
    return payload


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
        if start == -1 or end <= start:
            raise
        return json.loads(stripped[start : end + 1])


def _bounded_process_error(completed: subprocess.CompletedProcess[str]) -> str:
    detail = (completed.stderr or completed.stdout or "unknown error").strip()
    if completed.stdout:
        try:
            payload = json.loads(completed.stdout)
        except (TypeError, json.JSONDecodeError):
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get("result"), str):
            detail = payload["result"]
    return (
        f"Claude CLI exited with status {completed.returncode}: "
        f"{_bounded_text(detail)}"
    )


def _bounded_text(value: str) -> str:
    compact = " ".join(value.split())
    if len(compact) <= _ERROR_PREVIEW_LIMIT:
        return compact
    return compact[:_ERROR_PREVIEW_LIMIT] + "..."


def _field(value: Any, name: str) -> Any:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def _nonnegative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(int(value), 0)
    return 0


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _optional_string(value: Any) -> str | None:
    rendered = _string(value)
    return rendered or None
