"""Structured terminal-agent control plane for AutoCedar.

This module deliberately stays above the synthesis backend and below the
Textual UI.  The model proposes one validated ``AgentAction``; the UI/executor
performs it and emits user-visible events.  That boundary prevents chat text
from pretending that backend work has started.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


AgentActionKind = Literal[
    "respond",
    "help",
    "quit",
    "clear_transcript",
    "clear_draft",
    "start_draft",
    "append_requirements",
    "edit_draft",
    "show_draft",
    "save_draft",
    "author_current_draft",
    "author_spec",
    "verify_workspace",
    "synthesize",
    "show_schema",
    "show_policy",
    "show_artifacts",
    "show_models",
    "export_artifacts",
    "copy",
    "show_settings",
    "set_provider",
    "set_model",
    "set_effort",
    "set_api_key",
    "set_api_key_prompt",
    "clear_api_key",
    "api_key_status",
    "setup",
    "doctor",
    "answer_review",
    "edit_atom",
]


@dataclass(frozen=True)
class AgentState:
    """Compact state snapshot given to the planner."""

    active_task: str
    busy: bool
    drafting_active: bool
    draft_line_count: int
    draft_excerpt: list[str] = field(default_factory=list)
    pending_confirmation: str | None = None
    pending_review: str | None = None
    latest_session_dir: str | None = None
    latest_schema_path: str | None = None
    latest_policy_path: str | None = None
    latest_schema_exists: bool = False
    latest_policy_exists: bool = False
    latest_authoring_complete: bool = False
    latest_authoring_approved: bool | None = None
    latest_candidate_validated: bool | None = None
    latest_synthesis_converged: bool | None = None
    latest_synthesis_iterations: int | None = None
    latest_synthesis_loss: int | None = None
    latest_status_summary: str = ""
    provider: str = "codex"
    model: str = ""
    effort: str = "high"
    api_key_set: bool = False
    codex_auth_set: bool = False

    def to_prompt_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


class AgentAction(BaseModel):
    """One action proposed by the agent planner and performed by the executor."""

    model_config = ConfigDict(populate_by_name=True)

    kind: AgentActionKind
    message: str = ""
    content: str = ""
    path: str | None = None
    workspace: str | None = None
    spec: str | None = None
    out: str | None = None
    session_id: str | None = None
    schema_path: str | None = Field(default=None, alias="schema")
    provider: str | None = None
    model: str | None = None
    effort: str | None = None
    auto_approve: bool = False
    target: str | None = None
    mode: str | None = None
    value: str | None = None
    line: int | None = None
    scenarios: list[str] = Field(default_factory=list)
    run_id: str | None = None
    phase1_model: str | None = None
    phase2_model: str | None = None
    max_iters: int | None = None
    gen_references: bool = False
    no_review: bool = False
    review_key: str | None = None
    review_detail: str = ""
    confirmed: bool = False


class AgentPlanResponse(BaseModel):
    """Top-level planner response used for structured output."""

    action: AgentAction


@dataclass(frozen=True)
class AgentEvent:
    """Event emitted by the runtime/executor and rendered by the TUI."""

    kind: Literal[
        "assistant_text",
        "tool_call",
        "tool_result",
        "confirmation_required",
        "review_required",
        "progress",
        "error",
        "artifact_update",
    ]
    message: str
    action_kind: str | None = None


AGENT_PLANNER_SYSTEM = """\
You are AutoCedar's terminal-agent planner.

Return exactly one structured AgentAction. Do not write normal prose unless
the action kind is "respond". You do not execute tools yourself. You only choose
the next action; the AutoCedar executor performs it and reports the result.

Critical rules:
- Never claim that authoring, verification, saving, copying, setup, or review
  work has started in a respond message. Choose the matching action instead.
- If pending_review is set, route review commands to answer_review or edit_atom.
- You are the controller for all ordinary language. Even when drafting_active
  is true, decide whether the user input is policy content, conversation, or an
  operational request.
- If drafting_active is true and the user input contains policy requirements,
  choose append_requirements with the exact requirement text. Preserve pasted
  multiline requirement blocks.
- If the user asks to edit the working draft/spec, choose edit_draft. Supported
  modes: set_line with line and value, delete_line with line, insert_line with
  line and value, replace_all with value. Line numbers are 1-based.
- If drafting_active is true and the user asks to clear/delete/wipe/reset the
  draft, choose clear_draft. If they ask to show/save/author the draft, choose
  the corresponding action. Do not append operational requests as requirements.
- If the user says they want a policy/schema from requirements but has not
  pasted actual domain requirements, choose start_draft, not append_requirements.
- If the user asks to author the current draft, choose author_current_draft.
- If the user asks what to do next and a draft exists, respond concisely that
  they can author the current draft or save it first.
- Use show_schema, show_policy, show_artifacts, export_artifacts, or copy when
  users ask to inspect, export, copy, or retrieve generated artifacts or paths.
- Use show_models when users ask what models are available, and set_provider
  when they ask to switch between Anthropic and Codex.
- Use the current state fields to answer workflow-status questions. If
  latest_authoring_complete is true and latest_candidate_validated is true,
  you may say the generated candidate passed the recorded verification checks.
  If latest_policy_exists/latest_schema_exists are true, you may say those files
  exist and can be shown, copied, or exported.
- Keep authoring context clean: chat history is not policy input unless the user
  explicitly appends requirements to the draft.
"""


class ProviderAgentPlanner:
    """Provider-backed planner using Pydantic structured output."""

    def __init__(
        self,
        *,
        client: Any,
        model: str,
        effort: str,
        max_tokens: int = 1400,
    ) -> None:
        self.client = client
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens

    def plan(self, user_input: str, state: AgentState) -> AgentAction:
        prompt = (
            "Current AutoCedar state:\n"
            f"{state.to_prompt_json()}\n\n"
            "User input:\n"
            f"{user_input}"
        )
        try:
            response = self.client.messages.parse(
                model=self.model,
                max_tokens=self.max_tokens,
                thinking={"type": "adaptive"},
                output_config={"effort": self.effort},
                system=AGENT_PLANNER_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                output_format=AgentPlanResponse,
            )
            return response.parsed_output.action
        except Exception as exc:
            if not _should_use_json_retry(exc):
                raise
            return self._plan_with_json_retry(user_input, state)

    def _plan_with_json_retry(self, user_input: str, state: AgentState) -> AgentAction:
        schema_json = json.dumps(AgentPlanResponse.model_json_schema(), indent=2)
        prompt = (
            "Current AutoCedar state:\n"
            f"{state.to_prompt_json()}\n\n"
            "User input:\n"
            f"{user_input}\n\n"
            "Return only a JSON object matching this JSON Schema. Do not wrap it "
            "in Markdown and do not include explanatory prose.\n\n"
            f"{schema_json}"
        )
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            thinking={"type": "adaptive"},
            output_config={"effort": self.effort},
            system=AGENT_PLANNER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        payload = _loads_json_object(_first_text_block(response))
        try:
            return AgentPlanResponse.model_validate(payload).action
        except ValidationError:
            if isinstance(payload, dict) and "kind" in payload:
                return AgentAction.model_validate(payload)
            raise


def _should_use_json_retry(exc: Exception) -> bool:
    text = str(exc).lower()
    return "grammar compilation timed out" in text or "messages.parse" in text


def _first_text_block(response: Any) -> str:
    for block in getattr(response, "content", []):
        if getattr(block, "type", None) == "text":
            return str(getattr(block, "text", ""))
    return ""


def _loads_json_object(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])
