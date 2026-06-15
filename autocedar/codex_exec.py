"""Codex CLI-backed LLM adapter for internal AutoCedar experiments.

This adapter intentionally lets the Codex CLI own OpenAI/ChatGPT auth. A
researcher runs ``codex login`` once, then AutoCedar can call ``codex exec``
without reading or refreshing OAuth tokens itself.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from pydantic import BaseModel


DEFAULT_CODEX_MODEL = "gpt-5.5"
CODEX_PROVIDERS = {"codex", "openai-codex"}

_Runner = Callable[[list[str], str | None, Path], subprocess.CompletedProcess[str]]


def is_codex_provider(provider: str | None) -> bool:
    return (provider or "").strip().lower() in CODEX_PROVIDERS


def codex_reasoning_effort(effort: str | None) -> str:
    normalized = (effort or "high").strip().lower()
    if normalized == "max":
        return "xhigh"
    if normalized in {"low", "medium", "high", "xhigh"}:
        return normalized
    return "high"


class CodexExecClient:
    """Small subset of the Anthropic client shape used by ``LLMClient``."""

    def __init__(
        self,
        *,
        command: str | None = None,
        cwd: Path | str | None = None,
        runner: _Runner | None = None,
    ) -> None:
        self.command = command or os.environ.get("AUTOCEDAR_CODEX_BIN", "codex")
        self.cwd = Path(cwd or os.environ.get("AUTOCEDAR_CODEX_WORKDIR", os.getcwd()))
        self._runner = runner or self._default_runner
        self.messages = _CodexExecMessages(self)

    @staticmethod
    def _default_runner(
        cmd: list[str],
        prompt: str | None,
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            cmd,
            input=prompt,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )


class _CodexExecMessages:
    def __init__(self, parent: CodexExecClient) -> None:
        self._parent = parent

    def parse(self, **kwargs: Any) -> Any:
        output_format = kwargs.get("output_format")
        if not isinstance(output_format, type) or not issubclass(output_format, BaseModel):
            raise TypeError("CodexExecClient.parse requires a Pydantic output_format")

        text = self._run_codex(kwargs, output_format=output_format)
        try:
            payload = _loads_json_object(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Codex returned non-JSON structured output: {text}") from exc
        return SimpleNamespace(parsed_output=output_format.model_validate(payload))

    def create(self, **kwargs: Any) -> Any:
        text = self._run_codex(kwargs, output_format=None)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])

    def _run_codex(
        self,
        kwargs: dict[str, Any],
        *,
        output_format: type[BaseModel] | None,
        prompt_schema: dict[str, Any] | None = None,
    ) -> str:
        model = str(kwargs.get("model") or DEFAULT_CODEX_MODEL)
        effort = codex_reasoning_effort(_extract_effort(kwargs))
        strict_schema = _codex_strict_schema(output_format.model_json_schema()) if output_format else None
        prompt = _render_prompt(
            kwargs,
            structured=output_format is not None or prompt_schema is not None,
            prompt_schema=prompt_schema,
        )

        with tempfile.TemporaryDirectory(prefix="autocedar-codex-") as tmp:
            tmpdir = Path(tmp)
            out_path = tmpdir / "last-message.txt"
            cmd = [
                self._parent.command,
                "exec",
                "--ignore-user-config",
                "--ignore-rules",
                "--ephemeral",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "-m",
                model,
                "-c",
                f'model_reasoning_effort="{effort}"',
                "--output-last-message",
                str(out_path),
            ]
            if output_format is not None:
                schema_path = tmpdir / "output-schema.json"
                schema_path.write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )
                cmd.extend(["--output-schema", str(schema_path)])

            result = self._parent._runner(cmd, prompt, self._parent.cwd)
            if result.returncode != 0:
                if output_format is not None and "invalid_json_schema" in result.stderr:
                    return self._run_codex(
                        kwargs,
                        output_format=None,
                        prompt_schema=strict_schema,
                    )
                raise RuntimeError(
                    "Codex exec failed with exit code "
                    f"{result.returncode}.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
                )
            if not out_path.exists():
                raise RuntimeError(
                    "Codex exec completed but did not write --output-last-message.\n"
                    f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
                )
            return out_path.read_text(encoding="utf-8").strip()


def _extract_effort(kwargs: dict[str, Any]) -> str | None:
    output_config = kwargs.get("output_config")
    if isinstance(output_config, dict):
        effort = output_config.get("effort")
        if isinstance(effort, str):
            return effort
    return None


def _codex_strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Normalize Pydantic JSON Schema for Codex/OpenAI strict output mode."""
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


def _render_prompt(
    kwargs: dict[str, Any],
    *,
    structured: bool,
    prompt_schema: dict[str, Any] | None = None,
) -> str:
    parts = [
        "You are AutoCedar's internal LLM worker for Cedar policy-synthesis experiments.",
        "Do not edit files, run shell commands, browse the web, or inspect the repository.",
        "Use only the context in this prompt.",
    ]
    if structured:
        parts.append("Return exactly the JSON object requested by the provided output schema.")
    if prompt_schema is not None:
        parts.append(
            "The output schema is:\n"
            f"```json\n{json.dumps(prompt_schema, indent=2)}\n```\n"
            "Return only a JSON object. Do not wrap it in Markdown.",
        )

    system = kwargs.get("system")
    if system:
        parts.append("\n<SYSTEM>\n" + _render_content(system) + "\n</SYSTEM>")

    messages = kwargs.get("messages")
    if isinstance(messages, list):
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = str(message.get("role", "user")).upper()
            parts.append(f"\n<{role}>\n{_render_content(message.get('content'))}\n</{role}>")

    return "\n".join(parts).strip()


def _render_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        rendered: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    rendered.append(text)
            elif isinstance(item, str):
                rendered.append(item)
        return "\n\n".join(rendered)
    return str(content or "")


def _loads_json_object(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])
