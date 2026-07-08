"""Interactive Textual shell for AutoCedar."""

from __future__ import annotations

import contextlib
import datetime
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import threading
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Sequence

from rich.markup import escape
from rich.panel import Panel
from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual import events
from textual.message import Message
from textual.widgets import Footer, Header, Input, RichLog, Static

from autocedar.agent import AgentAction, AgentState, ProviderAgentPlanner
from autocedar.api_key import (
    format_api_key_validation_error,
    is_anthropic_auth_error,
    mask_api_key_for_display,
    normalize_anthropic_api_key,
    validate_anthropic_api_key,
)
from autocedar.codex_auth import (
    DEFAULT_CODEX_MODEL,
    CodexAuthClient,
    codex_auth_available,
    codex_auth_path,
    codex_runtime_info,
    is_codex_provider,
)
from autocedar.corpus import AtomDecision
from autocedar.env import (
    ANTHROPIC_API_KEY,
    is_real_anthropic_api_key,
    load_dotenv,
    remove_user_config_value,
    write_user_config_value,
)
from autocedar.harness_adapter import make_harness_synthesizer
from autocedar.llm import DEFAULT_EFFORT, LLMClient, default_model_for_provider, default_provider
from autocedar.pipeline import author as author_pipeline
from autocedar.progress import format_property_progress
from autocedar.property_atomizer import propose_property_atom
from autocedar.schema_atomizer import propose_schema_atoms
from autocedar.ui.terminal import (
    ReviewedAtom,
    _apply_field_edit,
    auto_approve,
    render_property_atom,
    render_property_reference,
    render_schema_atom,
    render_schema_declaration,
)


AMBER = "#f0c678"
COPPER = "#d99a5f"
CORAL = "#d57a5f"
CREAM = "#f3e6d3"
MUTED = "#bda98f"
TEAL = "#8fc9bd"
GREEN = "#98c379"
RED = "#e06c75"
DRAFT_PATH = Path("autocedar-spec.md")
COMMANDS = {
    "api-key",
    "apikey",
    "author",
    "artifacts",
    "clear",
    "copy",
    "doctor",
    "draft",
    "effort",
    "exit",
    "export",
    "help",
    "inspect",
    "model",
    "models",
    "new",
    "policy",
    "provider",
    "quit",
    "save",
    "schema",
    "search",
    "settings",
    "setup",
    "synthesize",
    "verify",
}

SLASH_COMMAND_DESCRIPTIONS = {
    "/author": "run HITL authoring for a spec or current draft",
    "/verify": "verify a workspace",
    "/synthesize": "run the synthesis harness",
    "/setup": "show Cedar/CVC5 install steps",
    "/doctor": "check API key and verifier setup",
    "/settings": "show provider, model, effort, and auth status",
    "/provider": "switch Anthropic or Codex",
    "/models": "show models available to the active provider",
    "/model": "set the default LLM model",
    "/effort": "set low, medium, high, or max effort",
    "/apikey": "set, show, or clear the saved API key",
    "/draft": "show, start, clear, edit, delete, or insert draft lines",
    "/artifacts": "show latest session/schema/policy paths",
    "/inspect": "show workflow state, verification status, and key artifact files",
    "/search": "search latest workflow/generated files",
    "/schema": "show latest or provided Cedar schema",
    "/policy": "show latest or provided Cedar policy",
    "/copy": "copy text or artifact paths",
    "/export": "export latest schema, policy, and transcript to a folder",
    "/save": "save the current draft",
    "/clear": "clear transcript or draft",
    "/new": "clear the current draft",
    "/help": "show full help",
    "/quit": "exit AutoCedar",
}

EFFORT_LEVELS = {"low", "medium", "high", "max"}


WELCOME_TEXT = f"""\
[bold {AMBER}]A U T O C E D A R[/]
[{CREAM}]Human-in-the-loop policy synthesis for production Cedar.[/]

[dim]Talk to the agent in normal language. Give it policy requirements,
ask it to verify a workspace, or tell it to author the current draft.
Drafting starts only after you approve it.[/]
"""


HELP_TEXT = """\
[bold #f0c678]AutoCedar[/]

Talk normally:

  [#f0c678]Start a policy draft[/]
  [#f0c678]Doctors can read records for patients on their care team.[/]
  [#f0c678]Save this as clinical.md[/]
  [#f0c678]Author this[/]
  [#f0c678]Author this with schema workspace/schema.cedarschema[/]
  [#f0c678]Verify the workspace[/]
  [#f0c678]Synthesize cedarbench/scenarios/realworld/emergency_break_glass no review[/]

Slash shortcuts are also available:

  [#f0c678]/author[/] [SPEC] [--out DIR] [--session-id ID] [--schema PATH] [--model MODEL] [--effort high]
  [#f0c678]/verify[/] [WORKSPACE]
  [#f0c678]/synthesize SCENARIO...[/] [--out DIR] [--max-iters N] [--no-review]
  [#f0c678]/setup[/]                 show local Cedar/CVC5 install steps
  [#f0c678]/doctor[/]                check API-key, Cedar SymCC, and CVC5 setup
  [#f0c678]/settings[/]              show provider, model, effort, and auth status
  [#f0c678]/provider anthropic|codex[/]
  [#f0c678]/models[/]                show available models for the active provider
  [#f0c678]/model MODEL[/]           set the default LLM model
  [#f0c678]/effort low|medium|high|max[/]
  [#f0c678]/apikey[/] [KEY|status|clear] set, show, or clear the saved API key
  [#f0c678]/draft[/] [show|start|clear] show, start, or clear draft capture
  [#f0c678]/draft edit 2 TEXT[/]      replace line 2 in the working draft
  [#f0c678]/draft delete 2[/]         delete line 2 from the working draft
  [#f0c678]/draft insert 2 TEXT[/]    insert TEXT before line 2
  [#f0c678]/artifacts[/]             show latest session/schema/policy paths
  [#f0c678]/inspect[/] [QUERY]       inspect workflow status and generated files
  [#f0c678]/search[/] [QUERY]        search latest workflow/generated files
  [#f0c678]/schema[/] [PATH]         show latest or provided Cedar schema
  [#f0c678]/policy[/] [PATH]         show latest or provided Cedar policy
  [#f0c678]/copy[/] last|transcript|session|schema|policy|draft [path] copy text or artifact path
  [#f0c678]/export[/] [DIR]          write schema, policy, transcript, and session path to a folder
  [#f0c678]/save[/] [PATH]           save the current draft
  [#f0c678]/new[/]                   clear the draft
  [#f0c678]/clear[/] [draft|transcript] clear transcript, or clear the draft explicitly
  [#f0c678]/quit[/]                  exit

During atom review, use one-line review commands:

  [#8fc9bd]A[/]                  approve
  [#d57a5f]R reason[/]           reject with reason
  [#f0c678]E field=value[/]      edit an atom field
  [#f0c678]E cedar_type=Bool[/]  fix a schema attribute type
  [#f0c678]E action=view[/]      fix a property action
  [#f0c678]E context.onCampusLan=Bool[/] add action request context
  [#f0c678]Q question[/]         record a question in the corpus
  [#f0c678]S[/]                  show the Cedar/schema declaration
  [#f0c678]V[/]                  view patch notes
"""


BRAND_TEXT = """\
[bold #f0c678]AUTOCEDAR[/]
[#bda98f]policy synthesis agent[/]

[bold #d99a5f]Pipeline[/]
[#8fc9bd]HITL[/] user atom review
[#8fc9bd]symcc[/] symbolic checks
[#8fc9bd]CEGIS[/] synthesis loop
"""


COMMAND_RAIL = """\
[bold #d99a5f]Try saying[/]

[#f0c678]start a policy draft[/]
[#f0c678]verify the workspace[/]
[#f0c678]show the draft[/]
[#f0c678]save this as spec.md[/]
[#f0c678]author this[/]
[#f0c678]author this with schema path[/]

[bold #d99a5f]Shortcuts[/]

[#f0c678]/author[/] spec.md
[#f0c678]/verify[/] workspace
[#f0c678]/synthesize[/] scenario
[#f0c678]/setup[/]
[#f0c678]/doctor[/]
[#f0c678]/settings[/]
[#f0c678]/provider[/] codex
[#f0c678]/models[/]
[#f0c678]/model[/] gpt-5.5
[#f0c678]/effort[/] high
[#f0c678]/apikey[/]
[#f0c678]/draft[/]
[#f0c678]/artifacts[/]
[#f0c678]/schema[/]
[#f0c678]/policy[/]
[#f0c678]/export[/]
[#f0c678]/copy[/] session
[#f0c678]/copy[/] last
[#f0c678]/copy[/] transcript
[#f0c678]/save[/]

[bold #d99a5f]Review keys[/]

[#8fc9bd]A[/] approve
[#d57a5f]R[/] reject
[#f0c678]E[/] edit
[#f0c678]Q[/] question
[#f0c678]S[/] show Cedar
"""


@dataclass
class AuthorOptions:
    spec: Path
    out: Path = Path("autocedar-runs")
    session_id: str | None = None
    schema: Path | None = None
    model: str | None = None
    effort: str | None = None
    auto_approve: bool = False


@dataclass
class SynthesizeOptions:
    scenarios: list[Path]
    out: Path = Path("eval_runs")
    run_id: str | None = None
    phase1_model: str | None = None
    phase2_model: str | None = None
    max_iters: int | None = None
    gen_references: bool = False
    no_review: bool = False


@dataclass
class ClipboardResult:
    ok: bool
    message: str


@dataclass
class PendingAction:
    summary: str
    run: Callable[[], None]


@dataclass
class ReviewRequest:
    atom: Any
    sequence: int
    index: int
    total: int | None
    stage_label: str
    current: Any = None
    edit_log: dict[str, Any] = field(default_factory=dict)
    event: threading.Event = field(default_factory=threading.Event)
    result: ReviewedAtom | None = None

    def __post_init__(self) -> None:
        self.current = self.atom


class CommandInput(Input):
    """Single-line command widget with explicit multiline paste forwarding."""

    class Pasted(Message):
        """A paste payload that should be handled as a submitted command."""

        def __init__(self, input_widget: "CommandInput", text: str) -> None:
            super().__init__()
            self.input_widget = input_widget
            self.text = text

    def _on_paste(self, event: events.Paste) -> None:
        if not event.text:
            event.stop()
            return
        if "\n" in event.text or "\r" in event.text:
            self.post_message(self.Pasted(self, event.text))
            event.stop()
            return
        super()._on_paste(event)


class TuiAtomReviewer:
    """Thread bridge from ``pipeline.author`` into the Textual app."""

    def __init__(self, app: "AutoCedarApp") -> None:
        self.app = app
        self.sequence = 0
        self.stage_label = "Atom review"
        self.stage_total: int | None = None
        self.stage_index = 0

    def begin_stage(self, label: str, total: int | None) -> None:
        self.stage_label = label
        self.stage_total = total
        self.stage_index = 0
        self.app.call_from_thread(self.app.begin_review_stage, label, total)

    def end_stage(self, label: str, approved: int, rejected: int) -> None:
        self.app.call_from_thread(
            self.app.end_review_stage,
            label,
            approved,
            rejected,
        )

    def schema_ready(self, schema_text: str) -> None:
        self.app.call_from_thread(self.app.show_schema_overview, schema_text)

    def property_plan_ready(self, properties: list[Any]) -> None:
        self.app.call_from_thread(self.app.show_property_overview, properties)

    def property_progress(self, payload: dict[str, Any]) -> None:
        self.app.call_from_thread(self.app.update_property_progress, payload)

    def __call__(self, atom: Any) -> ReviewedAtom:
        self.sequence += 1
        stage_label = self.stage_label
        self.stage_index += 1
        if self.stage_total is None:
            index = self.stage_index
            total = None
        else:
            if self.stage_index > self.stage_total:
                index = self.stage_index - self.stage_total
                total = None
                stage_label = f"{self.stage_label} replacement"
                self.app.call_from_thread(
                    self.app._say,
                    "Reviewing a replacement atom proposed after rejection.",
                )
            else:
                index = self.stage_index
                total = self.stage_total
        request = ReviewRequest(
            atom=atom,
            sequence=self.sequence,
            index=index,
            total=total,
            stage_label=stage_label,
        )
        self.app.call_from_thread(self.app.begin_review, request)
        request.event.wait()
        if request.result is None:
            return ReviewedAtom(
                atom=request.current,
                decision=AtomDecision(
                    atom_name=getattr(request.current, "name", "?"),
                    action="reject",
                    reason="TUI review ended without a decision",
                    edit_delta=request.edit_log,
                ),
            )
        return request.result


class AutoCedarApp(App[None]):
    """Full-screen interactive agent shell."""

    TITLE = "AutoCedar"
    SUB_TITLE = "HITL Cedar policy authoring"

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+l", "clear_log", "Clear"),
        Binding("tab", "complete_slash_command", "Complete", priority=True),
    ]

    CSS = """
    Screen {
        layout: vertical;
        background: #14100d;
        color: #f3e6d3;
    }

    Header {
        background: #231a13;
        color: #f0c678;
        text-style: bold;
    }

    Footer {
        background: #18130f;
        color: #bda98f;
    }

    #body {
        height: 1fr;
        padding: 1 1 0 1;
        background: #14100d;
    }

    #main {
        width: 1fr;
        height: 1fr;
    }

    #transcript {
        width: 1fr;
        height: 1fr;
        background: #171310;
        color: #f3e6d3;
        border: tall #d99a5f;
        padding: 1 2;
        scrollbar-background: #171310;
        scrollbar-color: #d99a5f;
    }

    #stream {
        display: none;
        width: 1fr;
        max-height: 8;
        margin-top: 1;
        padding: 0 2;
        background: #18120e;
        color: #f3e6d3;
        border: tall #8fc9bd;
    }

    #command_palette {
        display: none;
        width: 1fr;
        max-height: 10;
        margin-top: 1;
        padding: 0 2;
        background: #1d1712;
        color: #f3e6d3;
        border: tall #d99a5f;
    }

    #side {
        width: 38;
        min-width: 34;
        background: #18140f;
        border: tall #8fc9bd;
        padding: 1;
        margin-left: 1;
    }

    #brand {
        color: #f0c678;
        margin-bottom: 1;
    }

    #status_text {
        color: #f3e6d3;
        margin-bottom: 1;
    }

    #command_rail {
        color: #bda98f;
    }

    #command {
        height: 3;
        margin: 0 1 1 1;
        background: #18120e;
        color: #f3e6d3;
        border: tall #d99a5f;
    }

    #command:focus {
        border: tall #f0c678;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.draft_lines: list[str] = []
        self.drafting_active = False
        self.pending_review: ReviewRequest | None = None
        self.pending_action: PendingAction | None = None
        self.pending_secret: str | None = None
        self.llm_provider = default_provider()
        self.llm_model = _initial_model()
        self.llm_effort = _normalize_effort(os.environ.get("AUTOCEDAR_EFFORT")) or DEFAULT_EFFORT
        self.active_api_key = normalize_anthropic_api_key(os.environ.get(ANTHROPIC_API_KEY, ""))
        self.busy = False
        self.active_task = "idle"
        self.latest_session_dir: Path | None = None
        self.latest_schema_path: Path | None = None
        self.latest_policy_path: Path | None = None
        self.latest_authoring_complete = False
        self.latest_authoring_approved: bool | None = None
        self.latest_candidate_validated: bool | None = None
        self.latest_synthesis_converged: bool | None = None
        self.latest_synthesis_iterations: int | None = None
        self.latest_synthesis_loss: int | None = None
        self.latest_status_summary = ""
        self.property_progress_summary = "none"
        self.copyable_transcript: list[str] = []
        self.last_assistant_text = ""
        self.activity_message = ""
        self.activity_frame = 0
        self.agent_planner_factory: Callable[[], Any] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            with Vertical(id="main"):
                yield RichLog(
                    id="transcript",
                    markup=True,
                    highlight=True,
                    wrap=True,
                    auto_scroll=True,
                )
                yield Static("", id="stream")
                yield Static("", id="command_palette")
            with Vertical(id="side"):
                yield Static(BRAND_TEXT, id="brand")
                yield Static(id="status_text")
                yield Static(COMMAND_RAIL, id="command_rail")
        yield CommandInput(
            placeholder="Tell AutoCedar what to do, or type /help",
            id="command",
        )
        yield Footer()

    def on_mount(self) -> None:
        self._write(
            Panel(
                WELCOME_TEXT,
                title=f"[bold {COPPER}]online[/]",
                border_style=COPPER,
                padding=(1, 2),
            ),
        )
        self._write(
            f"[dim {MUTED}]Examples: verify the workspace; save this as spec.md; "
            "start a policy draft; author this; show the draft.[/]",
        )
        self._show_setup_hint_if_needed()
        self._update_status()
        self._clear_stream_output()
        self.set_interval(0.2, self._tick_activity)
        self.query_one(Input).focus()

    def action_clear_log(self) -> None:
        self.query_one("#transcript", RichLog).clear()
        self.copyable_transcript.clear()
        self.last_assistant_text = ""
        self._write(f"[dim {MUTED}]Transcript cleared.[/]")
        if self.draft_lines or self.drafting_active:
            self._write(
                f"[dim {MUTED}]Draft was not changed. Use /clear draft or /new "
                "to clear the working policy draft.[/]",
            )

    def action_complete_slash_command(self) -> None:
        command_input = self.query_one("#command", Input)
        completion = _slash_command_completion(command_input.value)
        if completion is None:
            return
        command_input.value = completion
        command_input.cursor_position = len(completion)
        self._show_command_palette(completion)

    def on_input_submitted(self, message: Input.Submitted) -> None:
        message.input.value = ""
        self._submit_command_text(message.value)

    def on_command_input_pasted(self, message: CommandInput.Pasted) -> None:
        message.input_widget.value = ""
        self._submit_command_text(message.text)

    def _submit_command_text(self, value: str) -> None:
        raw = value.strip()
        self._hide_command_palette()
        if not raw:
            return
        self.copyable_transcript.append(f"you > {_redact_sensitive_input(raw)}")
        self._write(
            f"[bold {TEAL}]you[/] [dim {MUTED}]>[/] "
            f"{escape(_redact_sensitive_input(raw))}",
        )
        if self.pending_secret == "api_key":
            self._handle_pending_api_key(raw)
            return
        if self.pending_review is not None:
            self._handle_review_input(raw)
            return
        if self.pending_action is not None:
            self._handle_confirmation_input(raw)
            return
        if self.busy:
            self._handle_busy_input(raw)
            return
        self._handle_shell_input(raw)

    def begin_review(self, request: ReviewRequest) -> None:
        self._stop_activity()
        self.pending_review = request
        self.active_task = request.stage_label.lower()
        self.query_one(Input).placeholder = "Review: A, R reason, E field=value, Q question, S, V"
        self._write(f"[bold {AMBER}]Review required before the agent continues.[/]")
        self._render_review_request(request)
        self._update_status()

    def begin_review_stage(self, label: str, total: int | None) -> None:
        if total is None:
            self._write(
                Panel(
                    (
                        f"{escape(label)} starts now.\n"
                        "AutoCedar may propose a small local property bundle, "
                        "but it verifies and reviews each atom one by one."
                    ),
                    title=f"[bold {COPPER}]Review stage[/]",
                    border_style=TEAL,
                    padding=(1, 2),
                ),
            )
            return
        if total <= 0:
            self._write(f"[dim {MUTED}]{escape(label)}: no atoms proposed.[/]")
            return
        next_step = (
            "After the last schema atom, AutoCedar composes the schema and shows an overview."
            if "schema" in label.lower()
            else "After the last property atom, AutoCedar compiles the verification plan."
        )
        self._write(
            Panel(
                (
                    f"{escape(label)} starts now.\n"
                    f"{total} atom(s) need a decision.\n"
                    f"{next_step}"
                ),
                title=f"[bold {COPPER}]Review stage[/]",
                border_style=TEAL,
                padding=(1, 2),
            ),
        )

    def end_review_stage(self, label: str, approved: int, rejected: int) -> None:
        next_step = (
            "Next: composing the schema."
            if "schema" in label.lower()
            else "Next: compiling the verification plan and running synthesis."
        )
        self._write(
            f"[bold {GREEN}]{escape(label)} complete.[/] "
            f"{approved} approved, {rejected} rejected. {next_step}",
        )

    def show_schema_overview(self, schema_text: str) -> None:
        overview = _schema_overview_text(schema_text)
        self._write(
            Panel(
                overview,
                title=f"[bold {COPPER}]Schema overview[/]",
                border_style=TEAL,
                padding=(1, 2),
            ),
        )

    def show_property_overview(self, properties: list[Any]) -> None:
        overview = _property_overview_text(properties)
        self._write(
            Panel(
                overview,
                title=f"[bold {COPPER}]Property overview[/]",
                border_style=TEAL,
                padding=(1, 2),
            ),
        )

    def update_property_progress(self, payload: dict[str, Any]) -> None:
        summary = format_property_progress(payload)
        self.property_progress_summary = summary
        event = str(payload.get("event") or "")
        if event in {
            "start",
            "source_start",
            "bundle_proposed",
            "coverage_blocked",
            "atom_decision",
            "source_complete",
            "complete",
            "stopped",
        }:
            style = CORAL if event in {"coverage_blocked", "stopped"} else TEAL
            self._write(
                f"[bold {style}]property progress[/] "
                f"[dim {MUTED}]>[/] {escape(summary)}",
            )
        self._update_status()

    def _handle_review_input(self, raw: str) -> None:
        request = self.pending_review
        if request is None:
            return

        key, detail = _split_review_input(raw)
        if key == "A":
            self._finish_review(request, "approve")
            return
        if key == "R":
            reason = detail or "Rejected in TUI review"
            self._finish_review(request, "reject", reason=reason)
            return
        if key == "E":
            if not detail:
                self._write(
                    f"[bold {RED}]Use E field=value.[/] "
                    "Examples: E cedar_type=Bool, E optional=true, "
                    "E context.onCampusLan=Bool, E action=view.",
                )
                return
            try:
                request.current = _apply_field_edit(
                    request.current,
                    detail,
                    request.edit_log,
                )
            except ValueError as exc:
                self._write(f"[bold {RED}]Edit rejected:[/] {escape(str(exc))}")
                return
            self._write(f"[bold {GREEN}]Atom updated.[/] Re-presenting.")
            self._render_review_request(request)
            return
        if key == "Q":
            if not detail:
                self._write(f"[bold {RED}]Use Q your question.[/]")
                return
            request.edit_log.setdefault("questions", []).append(detail)
            self._write(
                f"[{AMBER}]Question recorded in the review log. "
                "Live TUI Q/A will be wired in a later pass.[/]",
            )
            return
        if key == "S":
            cedar_text = _render_cedar_for_review(request.current)
            self._write(
                Panel(
                    Syntax(cedar_text, "cedar", word_wrap=True, theme="monokai"),
                    title=f"[bold {COPPER}]Cedar preview[/]",
                    border_style=TEAL,
                ),
            )
            return
        if key == "V":
            self._write(
                f"[dim {MUTED}]No Stage 1.5/2.5 patch view is available for this "
                "atom yet.[/]",
            )
            return
        self._write(f"[bold {RED}]Unknown review command.[/] Use A/R/E/Q/S/V.")

    def _finish_review(
        self,
        request: ReviewRequest,
        action: str,
        *,
        reason: str = "",
    ) -> None:
        request.result = ReviewedAtom(
            atom=request.current,
            decision=AtomDecision(
                atom_name=getattr(request.current, "name", "?"),
                action=action,
                reason=reason,
                intent_acknowledged_by_user=(action == "approve"),
                symbolic_verified=getattr(request.current, "symbolic_verified", False),
                edit_delta=request.edit_log,
            ),
        )
        request.event.set()
        self.pending_review = None
        self.query_one(Input).placeholder = "Tell AutoCedar what to do, or type /help"
        if action == "approve":
            self._write(f"[bold {GREEN}]Review approve recorded.[/] Continuing.")
        elif request.current.__class__.__name__ == "PropertyAtom":
            self._write(
                f"[bold {CORAL}]Review reject recorded.[/] "
                "I’ll ask for a replacement property atom if repair is available.",
            )
        else:
            self._write(f"[bold {CORAL}]Review reject recorded.[/] Continuing.")
        self.active_task = "authoring" if self.busy else "idle"
        self._update_status()

    def _request_confirmation(self, summary: str, run: Callable[[], None]) -> None:
        if self.busy:
            self._write(f"[{AMBER}]The agent is already running a task.[/]")
            return
        self.pending_action = PendingAction(summary=summary, run=run)
        self.active_task = "awaiting confirmation"
        self.query_one(Input).placeholder = "Say yes to proceed, or no to cancel"
        self._say(f"{summary}\n\nProceed? Say “yes” to continue or “no” to cancel.")
        self._update_status()

    def _handle_confirmation_input(self, raw: str) -> None:
        pending = self.pending_action
        if pending is None:
            return
        answer = _squash(raw).lower()
        if answer in {"yes", "y", "yeah", "yep", "proceed", "continue", "do it", "run it", "go"}:
            self.pending_action = None
            self.query_one(Input).placeholder = "Tell AutoCedar what to do, or type /help"
            self._say("Proceeding.")
            pending.run()
            return
        if answer in {"no", "n", "nope", "cancel", "stop", "abort", "never mind", "nevermind"}:
            self.pending_action = None
            self.active_task = "idle"
            self.query_one(Input).placeholder = "Tell AutoCedar what to do, or type /help"
            self._say("Cancelled.")
            self._update_status()
            return
        self._say("Please answer “yes” to proceed or “no” to cancel.")

    def _handle_busy_input(self, raw: str) -> None:
        lowered = _squash(raw).lower()
        if lowered in {"status", "what is happening", "what's happening", "wait", "help"}:
            self._say(
                f"I’m still working on `{self.active_task}`. "
                "When the next atom review is ready, I’ll show the A/R/E/Q/S/V review card.",
            )
            return
        if lowered in {"a", "approve", "r", "reject", "s", "show", "v", "q"} or raw.startswith("/"):
            self._say(
                f"I’m still working on `{self.active_task}`. "
                "Review commands are only active after an atom review card is visible.",
            )
            return
        self._say(
            f"I’m still working on `{self.active_task}`. "
            "Wait for the next atom review card before sending more input.",
        )

    def _handle_shell_input(self, raw: str) -> None:
        stripped = raw.strip()
        if stripped.startswith("+"):
            self._handle_explicit_draft_line(stripped[1:].strip())
            return
        if not raw.startswith("/"):
            self._handle_natural_language_input(raw)
            return
        self._handle_command_input(raw)

    def on_input_changed(self, message: Input.Changed) -> None:
        value = message.value
        if value.startswith("/") and self.pending_review is None:
            self._show_command_palette(value)
        else:
            self._hide_command_palette()

    def _handle_natural_language_input(self, raw: str) -> None:
        if self.agent_planner_factory or self._planner_provider_ready():
            self._start_agent_planning(raw)
            return
        if is_codex_provider(self.llm_provider):
            self._say(
                "Natural-language control is set to Codex, but no local Codex "
                "OAuth session is available. Run `codex login`, then try again, "
                "or switch providers with /provider anthropic.",
            )
        else:
            self._say(
                "Natural-language control needs the live agent planner. Run /apikey "
                "to add your Anthropic API key, or switch providers with /provider codex "
                "after running `codex login`.",
            )

    def _planner_provider_ready(self) -> bool:
        if is_codex_provider(self.llm_provider):
            return codex_auth_available()
        return is_real_anthropic_api_key(self._active_api_key())

    def _start_agent_planning(self, raw: str) -> None:
        if self.busy:
            self._handle_busy_input(raw)
            return
        state = self._agent_state()
        self.busy = True
        self.active_task = "model planning"
        self.query_one(Input).placeholder = "AutoCedar is thinking..."
        self._update_status()
        self._start_activity("model planning")
        self.run_worker(
            lambda: self._plan_and_execute_agent(raw, state),
            thread=True,
            exclusive=False,
            exit_on_error=False,
        )

    def _plan_and_execute_agent(self, raw: str, state: AgentState) -> None:
        try:
            planner = self._make_agent_planner()
            action = planner.plan(raw, state)
        except Exception as exc:
            self.call_from_thread(self._finish_agent_planning, None, exc)
            return
        self.call_from_thread(self._finish_agent_planning, action, None)

    def _finish_agent_planning(
        self,
        action: AgentAction | None,
        error: Exception | None,
    ) -> None:
        self.busy = False
        self._stop_activity()
        self.active_task = "idle"
        self.query_one(Input).placeholder = "Tell AutoCedar what to do, or type /help"
        self._update_status()
        if error is not None:
            if is_anthropic_auth_error(error):
                remove_user_config_value(ANTHROPIC_API_KEY)
                self.active_api_key = ""
                os.environ.pop(ANTHROPIC_API_KEY, None)
                self._update_status()
            self._say(_agent_failure_message(error))
            return
        if action is None:
            self._say("The planner returned no action.")
            return
        self._execute_agent_action(action)

    def _make_agent_planner(self) -> Any:
        if self.agent_planner_factory is not None:
            return self.agent_planner_factory()
        return ProviderAgentPlanner(
            client=self._make_provider_client(),
            model=self.llm_model,
            effort=self.llm_effort,
        )

    def _make_provider_client(self) -> Any:
        if is_codex_provider(self.llm_provider):
            return CodexAuthClient()
        return self._make_anthropic_client()

    def _agent_state(self) -> AgentState:
        review_summary = None
        if self.pending_review is not None:
            atom_name = getattr(self.pending_review.current, "name", "?")
            review_summary = f"{self.pending_review.stage_label}: {atom_name}"
        return AgentState(
            active_task=self.active_task,
            busy=self.busy,
            drafting_active=self.drafting_active,
            draft_line_count=len(self.draft_lines),
            draft_excerpt=self.draft_lines[-8:],
            pending_confirmation=self.pending_action.summary if self.pending_action else None,
            pending_review=review_summary,
            latest_session_dir=str(self.latest_session_dir) if self.latest_session_dir else None,
            latest_schema_path=str(self.latest_schema_path) if self.latest_schema_path else None,
            latest_policy_path=str(self.latest_policy_path) if self.latest_policy_path else None,
            latest_schema_exists=bool(self.latest_schema_path and self.latest_schema_path.exists()),
            latest_policy_exists=bool(self.latest_policy_path and self.latest_policy_path.exists()),
            latest_authoring_complete=self.latest_authoring_complete,
            latest_authoring_approved=self.latest_authoring_approved,
            latest_candidate_validated=self.latest_candidate_validated,
            latest_synthesis_converged=self.latest_synthesis_converged,
            latest_synthesis_iterations=self.latest_synthesis_iterations,
            latest_synthesis_loss=self.latest_synthesis_loss,
            latest_status_summary=self.latest_status_summary,
            tools=_agent_tool_catalog(),
            provider=self.llm_provider,
            model=self.llm_model,
            effort=self.llm_effort,
            api_key_set=is_real_anthropic_api_key(self._active_api_key()),
            codex_auth_set=codex_auth_available(),
        )

    def _agent_action_from_command(
        self,
        command: str,
        args: Sequence[str],
    ) -> AgentAction | None:
        if command == "help":
            return AgentAction(kind="help")
        if command == "clear":
            target = args[0].lower() if args else "transcript"
            if target in {"draft", "spec", "policy"}:
                return AgentAction(kind="clear_draft")
            if target in {"transcript", "screen", "chat", "log"}:
                return AgentAction(kind="clear_transcript")
            raise ValueError("Use /clear transcript or /clear draft.")
        if command == "settings":
            return AgentAction(kind="show_settings")
        if command == "provider":
            return (
                AgentAction(kind="set_provider", provider=args[0])
                if args
                else AgentAction(kind="show_settings")
            )
        if command == "models":
            return AgentAction(kind="show_models")
        if command == "setup":
            return AgentAction(kind="setup")
        if command == "doctor":
            return AgentAction(kind="doctor")
        if command == "model":
            return AgentAction(kind="set_model", model=args[0]) if args else AgentAction(kind="show_settings")
        if command == "effort":
            return AgentAction(kind="set_effort", effort=args[0]) if args else AgentAction(kind="show_settings")
        if command in {"apikey", "api-key"}:
            if not args:
                return AgentAction(kind="set_api_key_prompt")
            value = args[0]
            if value.lower() in {"clear", "unset", "remove", "delete"}:
                return AgentAction(kind="clear_api_key")
            if value.lower() in {"status", "show"}:
                return AgentAction(kind="api_key_status")
            return AgentAction(kind="set_api_key", value=value)
        if command == "new":
            return AgentAction(kind="clear_draft")
        if command == "draft":
            target = args[0].lower() if args else ""
            if target in {"clear", "reset", "wipe", "new"}:
                return AgentAction(kind="clear_draft")
            if target in {"start", "capture", "begin"}:
                return AgentAction(kind="start_draft", confirmed=True)
            if target in {"show", "view"}:
                return AgentAction(kind="show_draft")
            if target in {"edit", "set", "replace"}:
                if len(args) < 3:
                    raise ValueError("Use /draft edit LINE replacement text.")
                return AgentAction(
                    kind="edit_draft",
                    mode="set_line",
                    line=_parse_line_number(args[1]),
                    value=" ".join(args[2:]),
                )
            if target in {"delete", "del", "remove"}:
                if len(args) != 2:
                    raise ValueError("Use /draft delete LINE.")
                return AgentAction(
                    kind="edit_draft",
                    mode="delete_line",
                    line=_parse_line_number(args[1]),
                )
            if target in {"insert", "add"}:
                if len(args) < 3:
                    raise ValueError("Use /draft insert LINE text to insert.")
                return AgentAction(
                    kind="edit_draft",
                    mode="insert_line",
                    line=_parse_line_number(args[1]),
                    value=" ".join(args[2:]),
                )
            if target == "":
                return AgentAction(
                    kind="show_draft" if self.drafting_active or self.draft_lines else "start_draft",
                    confirmed=not self.drafting_active and not self.draft_lines,
                )
            raise ValueError(
                "Use /draft, /draft show, /draft start, /draft clear, "
                "/draft edit LINE TEXT, /draft delete LINE, or /draft insert LINE TEXT.",
            )
        if command == "artifacts":
            return AgentAction(kind="show_artifacts")
        if command == "inspect":
            return AgentAction(kind="inspect_workflow", content=" ".join(args))
        if command == "search":
            return AgentAction(kind="search_artifacts", content=" ".join(args))
        if command == "schema":
            return AgentAction(kind="show_schema", path=str(args[0]) if args else None)
        if command == "policy":
            return AgentAction(kind="show_policy", path=str(args[0]) if args else None)
        if command == "copy":
            if not args:
                raise ValueError(
                    "Use /copy last, /copy transcript, /copy session, /copy schema, "
                    "/copy schema path, /copy policy, /copy policy path, or /copy draft.",
                )
            if args[0].lower() in {"path", "text"}:
                return AgentAction(
                    kind="copy",
                    target=args[0],
                    value=" ".join(args[1:]),
                )
            return AgentAction(
                kind="copy",
                target=args[0],
                mode=args[1] if len(args) > 1 else None,
            )
        if command == "export":
            return AgentAction(kind="export_artifacts", path=str(args[0]) if args else None)
        if command == "save":
            return AgentAction(kind="save_draft", path=str(args[0]) if args else None)
        if command in {"quit", "exit"}:
            return AgentAction(kind="quit")
        if command == "verify":
            return AgentAction(kind="verify_workspace", workspace=str(args[0]) if args else "workspace")
        if command == "author":
            if args:
                if args[0].startswith("--"):
                    if not self.draft_lines:
                        raise ValueError(
                            "Draft is empty. Use /author SPEC, or start a draft and add requirements first.",
                        )
                    return _agent_action_from_author_options(
                        parse_author_args([str(DRAFT_PATH), *args]),
                        from_draft=True,
                    )
                return _agent_action_from_author_options(parse_author_args(args), from_draft=False)
            if not self.draft_lines:
                raise ValueError("Draft is empty. Use /author SPEC, or start a draft and add requirements first.")
            return AgentAction(kind="author_current_draft", spec=str(DRAFT_PATH))
        if command == "synthesize":
            return _agent_action_from_synthesize_options(parse_synthesize_args(args))
        return None

    def _execute_agent_action(self, action: AgentAction) -> None:
        try:
            if action.kind == "help":
                self._say(HELP_TEXT)
            elif action.kind == "respond":
                self._say(escape(action.message or ""))
            elif action.kind == "quit":
                self._say("I’ll close the session.")
                self.exit()
            elif action.kind == "clear_transcript":
                self.action_clear_log()
            elif action.kind == "clear_draft":
                self._request_confirmation(
                    "I’m going to clear the working policy draft.",
                    self._clear_draft,
                )
            elif action.kind == "start_draft":
                if self.drafting_active:
                    self._say(
                        "Drafting is already active. Paste natural-language requirements "
                        "and I’ll add those lines to the working draft.",
                    )
                elif action.confirmed:
                    self._start_drafting()
                else:
                    self._request_confirmation(
                        _describe_start_draft_action(),
                        self._start_drafting,
                    )
            elif action.kind == "append_requirements":
                if not self.drafting_active:
                    self._request_confirmation(
                        _describe_start_draft_action(),
                        self._start_drafting,
                    )
                else:
                    self._append_draft_text(action.content)
            elif action.kind == "edit_draft":
                self._edit_draft(
                    mode=action.mode,
                    line=action.line,
                    value=action.value,
                )
            elif action.kind == "show_draft":
                self._show_draft()
            elif action.kind == "save_draft":
                args = [action.path] if action.path else []
                path = Path(action.path) if action.path else DRAFT_PATH
                self._request_confirmation(
                    f"I’m going to save the current draft to {path}.",
                    lambda args=args: self._save_draft(args),
                )
            elif action.kind == "verify_workspace":
                workspace = Path(action.workspace or "workspace")
                self._request_confirmation(
                    (
                        f"I’m going to verify {workspace} with Cedar symcc. "
                        "This checks the existing candidate against the workspace verification plan."
                    ),
                    lambda workspace=workspace: self._start_task(
                        f"verify {workspace}",
                        lambda: self._verify_workspace(workspace),
                    ),
                )
            elif action.kind in {"author_current_draft", "author_spec"}:
                options = self._resolve_author_options(_author_options_from_agent_action(action))
                from_draft = action.kind == "author_current_draft"
                if from_draft and not self.draft_lines:
                    raise ValueError("Draft is empty. Start a draft and paste requirements before authoring.")
                self._request_confirmation(
                    _describe_author_action(options, from_draft=from_draft),
                    lambda options=options, from_draft=from_draft: self._run_author_action(
                        options,
                        from_draft=from_draft,
                    ),
                )
            elif action.kind == "synthesize":
                options = self._resolve_synthesize_options(_synthesize_options_from_agent_action(action))
                self._request_confirmation(
                    _describe_synthesize_action(options),
                    lambda options=options: self._start_task(
                        "synthesize",
                        lambda: self._synthesize(options),
                    ),
                )
            elif action.kind == "show_schema":
                self._show_schema_command([action.path] if action.path else [])
            elif action.kind == "show_policy":
                self._show_policy_command([action.path] if action.path else [])
            elif action.kind == "show_artifacts":
                self._show_artifacts()
            elif action.kind == "inspect_workflow":
                self._inspect_workflow(action.content or action.message)
            elif action.kind == "search_artifacts":
                self._search_artifacts(action.content or action.message)
            elif action.kind == "show_models":
                self._show_models()
            elif action.kind == "export_artifacts":
                self._export_artifacts(Path(action.path) if action.path else None)
            elif action.kind == "copy":
                args = [action.target or ""]
                if action.mode:
                    args.append(action.mode)
                if action.value and action.target in {"path", "text"}:
                    args.extend(action.value.split())
                self._handle_copy_command([arg for arg in args if arg])
            elif action.kind == "show_settings":
                self._show_settings()
            elif action.kind == "set_provider":
                if not action.provider:
                    raise ValueError("Provider must be anthropic or codex.")
                self._set_provider(action.provider)
            elif action.kind == "set_model":
                if not action.model:
                    raise ValueError("Model cannot be empty.")
                self._set_model(action.model)
            elif action.kind == "set_effort":
                if not action.effort:
                    raise ValueError("Effort must be one of: low, medium, high, max.")
                self._set_effort(action.effort)
            elif action.kind == "set_api_key":
                if not action.value:
                    raise ValueError("API key cannot be empty.")
                self._set_api_key(action.value)
            elif action.kind == "set_api_key_prompt":
                self._handle_api_key_command([])
            elif action.kind == "clear_api_key":
                self._clear_api_key()
            elif action.kind == "api_key_status":
                self._show_api_key_status()
            elif action.kind == "setup":
                self._show_setup_plan()
            elif action.kind == "doctor":
                self._show_doctor_report()
            elif action.kind in {"answer_review", "edit_atom"}:
                self._handle_review_input(
                    f"{action.review_key or 'Q'} {action.review_detail}".strip(),
                )
            else:
                raise ValueError(f"Unsupported agent action: {action.kind}")
        except ValueError as exc:
            self._write(f"[bold {RED}]{escape(str(exc))}[/]")

    def _handle_command_input(self, raw: str) -> None:
        try:
            tokens = tokenize(raw)
        except ValueError as exc:
            self._write(f"[bold {RED}]Could not parse input:[/] {escape(str(exc))}")
            return
        if not tokens:
            return

        command = tokens[0].lstrip("/").lower()
        args = tokens[1:]
        if command not in COMMANDS:
            self._say("I don’t recognize that shortcut. Try /help.")
            return

        try:
            action = self._agent_action_from_command(command, args)
            if action is not None:
                self._execute_agent_action(action)
                return
            raise ValueError(f"Unsupported shortcut: /{command}")
        except ValueError as exc:
            self._write(f"[bold {RED}]{escape(str(exc))}[/]")

    def _handle_explicit_draft_line(self, line: str) -> None:
        if not line:
            self._write(f"[bold {RED}]Use + followed by the requirement text.[/]")
            return
        if not self.drafting_active:
            self.drafting_active = True
        self._append_draft_text(line)

    def _handle_api_key_command(self, args: Sequence[str]) -> None:
        if not args:
            self.pending_secret = "api_key"
            self.query_one(Input).placeholder = "Paste ANTHROPIC_API_KEY, or type cancel"
            self._say(
                "Paste your Anthropic API key. I’ll redact it in the transcript "
                "and validate it before saving it to the user-level AutoCedar config. "
                "Type “cancel” to stop.",
            )
            self._update_status()
            return
        value = args[0]
        if value.lower() in {"clear", "unset", "remove", "delete"}:
            self._clear_api_key()
            return
        if value.lower() in {"status", "show"}:
            self._show_api_key_status()
            return
        self._set_api_key(value)

    def _handle_pending_api_key(self, raw: str) -> None:
        value = raw.strip()
        self.pending_secret = None
        self.query_one(Input).placeholder = "Tell AutoCedar what to do, or type /help"
        if value.lower() in {"cancel", "stop", "abort", "no"}:
            self._say("Cancelled API key entry.")
            self._update_status()
            return
        self._set_api_key(value)

    def _set_provider(self, provider: str) -> None:
        normalized = provider.strip().lower()
        if normalized in {"anthropic", "claude"}:
            self.llm_provider = "anthropic"
            if self.llm_model.startswith("gpt-"):
                self.llm_model = default_model_for_provider("anthropic")
        elif normalized in {"codex", "openai-codex", "openai"}:
            self.llm_provider = "codex"
            if self.llm_model.startswith("claude-"):
                self.llm_model = os.environ.get("AUTOCEDAR_CODEX_MODEL", DEFAULT_CODEX_MODEL)
        else:
            raise ValueError("Provider must be anthropic or codex.")
        os.environ["AUTOCEDAR_PROVIDER"] = self.llm_provider
        os.environ["AUTOCEDAR_MODEL"] = self.llm_model
        os.environ["AUTOCEDAR_CHAT_MODEL"] = self.llm_model
        os.environ["AUTOCEDAR_AUTHOR_MODEL"] = self.llm_model
        if is_codex_provider(self.llm_provider):
            auth_note = (
                "Codex OAuth is available."
                if codex_auth_available()
                else "Run `codex login` before natural-language planning."
            )
            self._say(
                f"Provider set to [bold {AMBER}]Codex[/] with model "
                f"[bold {AMBER}]{escape(self.llm_model)}[/]. {auth_note}",
            )
        else:
            self._say(
                f"Provider set to [bold {AMBER}]Anthropic[/] with model "
                f"[bold {AMBER}]{escape(self.llm_model)}[/].",
            )
        self._update_status()

    def _show_models(self) -> None:
        if is_codex_provider(self.llm_provider):
            info = codex_runtime_info()
            if info.auth_available:
                body = _codex_models_text(info)
            else:
                body = "\n".join([
                    f"[bold {CORAL}]Codex OAuth is not available.[/]",
                    f"Expected auth file: {escape(info.auth_source)}",
                    f"Base URL: {escape(info.base_url)}",
                    "",
                    "Run `codex login` once, then use /provider codex and /models again.",
                    "",
                    f"[dim {MUTED}]{escape(info.error or '')}[/]",
                ])
            self._write(
                Panel(
                    body,
                    title=f"[bold {COPPER}]Codex models[/]",
                    border_style=TEAL if info.auth_available else CORAL,
                    padding=(1, 2),
                ),
            )
            return
        body = "\n".join([
            f"[dim {MUTED}]provider[/]\n[bold {CREAM}]anthropic[/]",
            f"[dim {MUTED}]current model[/]\n[bold {CREAM}]{escape(self.llm_model)}[/]",
            f"[dim {MUTED}]thinking[/]\n[bold {CREAM}]low, medium, high, max[/]",
            "",
            "AutoCedar does not call an Anthropic model-list endpoint. Use /model MODEL to set a model.",
        ])
        self._write(
            Panel(
                body,
                title=f"[bold {COPPER}]Anthropic models[/]",
                border_style=TEAL,
                padding=(1, 2),
            ),
        )

    def _set_model(self, model: str) -> None:
        normalized = model.strip()
        if not normalized:
            raise ValueError("Model cannot be empty.")
        self.llm_model = normalized
        os.environ["AUTOCEDAR_MODEL"] = normalized
        os.environ["AUTOCEDAR_CHAT_MODEL"] = normalized
        os.environ["AUTOCEDAR_AUTHOR_MODEL"] = normalized
        self._say(f"Model set to [bold {AMBER}]{escape(normalized)}[/].")
        self._update_status()

    def _set_effort(self, effort: str) -> None:
        normalized = _normalize_effort(effort)
        if normalized is None:
            raise ValueError("Effort must be one of: low, medium, high, max.")
        self.llm_effort = normalized
        os.environ["AUTOCEDAR_EFFORT"] = normalized
        self._say(f"Effort set to [bold {AMBER}]{normalized}[/].")
        self._update_status()

    def _set_api_key(self, api_key: str) -> None:
        value = normalize_anthropic_api_key(api_key)
        if not value:
            raise ValueError("API key cannot be empty.")
        if not is_real_anthropic_api_key(value):
            raise ValueError(
                "That does not look like a real Anthropic API key. "
                "Paste the full key from the Anthropic console, not a redacted value.",
            )
        self._say("Checking Anthropic API key before saving it...")
        try:
            validate_anthropic_api_key(value, model=self.llm_model)
        except Exception as exc:
            raise ValueError(format_api_key_validation_error(exc, model=self.llm_model)) from exc
        path = write_user_config_value(ANTHROPIC_API_KEY, value)
        self.active_api_key = value
        os.environ[ANTHROPIC_API_KEY] = value
        self._say(
            "Anthropic API key saved "
            f"([dim {MUTED}]{escape(mask_api_key_for_display(value))}[/]) to "
            f"[dim {MUTED}]{escape(str(path))}[/].",
        )
        self._update_status()

    def _clear_api_key(self) -> None:
        path = remove_user_config_value(ANTHROPIC_API_KEY)
        self.active_api_key = ""
        self._say(f"Anthropic API key removed from [dim {MUTED}]{escape(str(path))}[/].")
        self._update_status()

    def _active_api_key(self) -> str:
        if is_real_anthropic_api_key(self.active_api_key):
            return self.active_api_key
        return normalize_anthropic_api_key(os.environ.get(ANTHROPIC_API_KEY, ""))

    def _show_api_key_status(self) -> None:
        key = self._active_api_key()
        if is_real_anthropic_api_key(key):
            self._say(
                "Active Anthropic API key is set for this session "
                f"([dim {MUTED}]{escape(mask_api_key_for_display(key))}[/]).",
            )
        else:
            self._say("No active Anthropic API key is set for this session.")
        self._update_status()

    def _show_settings(self) -> None:
        self._write(
            Panel(
                self._settings_text(),
                title=f"[bold {COPPER}]Runtime settings[/]",
                border_style=TEAL,
                padding=(1, 2),
            ),
        )

    def _show_setup_hint_if_needed(self) -> None:
        from autocedar.setup_tools import build_setup_plan

        plan = build_setup_plan()
        if not plan.needs_install and not plan.blocked:
            return
        self._write(
            Panel(
                f"[bold {AMBER}]Verifier setup is incomplete.[/]\n\n"
                f"Type [bold {AMBER}]/setup[/] to see the exact Cedar/CVC5 install steps, "
                f"then run [bold {AMBER}]autocedar setup --yes[/] from your terminal if you want AutoCedar to install what it can.\n"
                f"Type [bold {AMBER}]/doctor[/] anytime to re-check the environment.",
                title=f"[bold {COPPER}]setup needed[/]",
                border_style=AMBER,
                padding=(1, 2),
            ),
        )

    def _show_setup_plan(self) -> None:
        from autocedar.setup_tools import build_setup_plan, format_setup_plan

        self._write(
            Panel(
                format_setup_plan(build_setup_plan()),
                title=f"[bold {COPPER}]Verifier setup[/]",
                border_style=TEAL,
                padding=(1, 2),
            ),
        )

    def _show_doctor_report(self) -> None:
        from autocedar.doctor import format_doctor_report, run_doctor

        self._write(
            Panel(
                format_doctor_report(run_doctor()),
                title=f"[bold {COPPER}]Doctor[/]",
                border_style=TEAL,
                padding=(1, 2),
            ),
        )

    def _settings_text(self) -> str:
        api_key = self._active_api_key()
        api_key_is_real = is_real_anthropic_api_key(api_key)
        codex_selected = is_codex_provider(self.llm_provider)
        codex_auth = codex_auth_available() if codex_selected else False
        auth_label = "Codex OAuth"
        auth_state = "set" if codex_auth else "not set"
        auth_color = TEAL if codex_auth else CORAL
        return "\n".join(
            [
                f"[dim {MUTED}]provider[/]\n[bold {CREAM}]{escape(self.llm_provider)}[/]",
                f"[dim {MUTED}]model[/]\n[bold {CREAM}]{escape(self.llm_model)}[/]",
                f"[dim {MUTED}]effort[/]\n[bold {CREAM}]{escape(self.llm_effort)}[/]",
                (
                    f"[dim {MUTED}]{auth_label}[/]\n[bold {auth_color}]{auth_state}[/]\n"
                    f"[dim {MUTED}]source: {escape(str(codex_auth_path()))}[/]"
                    if codex_selected
                    else
                    f"[dim {MUTED}]api key[/]\n[bold {TEAL}]set[/] "
                    f"[dim {MUTED}]({_mask_api_key(api_key)})[/]"
                    if api_key_is_real
                    else f"[dim {MUTED}]api key[/]\n[bold {CORAL}]not set[/]"
                ),
                "",
                f"[dim {MUTED}]Use /provider, /models, /model, /effort, or /apikey to change these.[/]",
            ],
        )

    def _resolve_author_options(self, options: AuthorOptions) -> AuthorOptions:
        return replace(
            options,
            model=options.model or self.llm_model,
            effort=options.effort or self.llm_effort,
        )

    def _resolve_synthesize_options(self, options: SynthesizeOptions) -> SynthesizeOptions:
        return replace(
            options,
            phase1_model=options.phase1_model or self.llm_model,
            phase2_model=options.phase2_model or self.llm_model,
        )

    def _show_draft(self) -> None:
        if not self.draft_lines:
            if self.drafting_active:
                self._write(
                    f"[dim {MUTED}]Draft capture is active, but no lines have been "
                    "captured yet. Type a requirement, or prefix it with + to force "
                    "capture.[/]",
                )
                return
            self._write(
                f"[dim {MUTED}]Draft is empty. Say “start a policy draft” or type "
                "/draft to begin.[/]",
            )
            return
        self._write(
            Panel(
                _numbered_draft_text(self.draft_lines),
                title=f"[bold {COPPER}]Current draft[/]",
                border_style=TEAL,
                padding=(1, 2),
            ),
        )

    def _show_artifacts(self) -> None:
        rows = [
            ("session", self.latest_session_dir),
            ("schema", self.latest_schema_path),
            ("policy", self.latest_policy_path),
        ]
        if not any(path for _, path in rows):
            self._write(
                f"[dim {MUTED}]No authoring artifacts are registered yet. "
                "Run authoring first, or pass a path to /schema or /policy.[/]",
            )
            return
        lines = []
        for label, path in rows:
            value = str(path) if path else "(not available)"
            lines.append(f"[bold {AMBER}]{label}[/]: {escape(value)}")
        if self.latest_status_summary:
            lines.extend(["", f"[bold {AMBER}]status[/]: {escape(self.latest_status_summary)}"])
        lines.extend([
            "",
            f"[dim {MUTED}]Use /schema, /policy, /export, /copy schema path, or /copy policy path.[/]",
        ])
        self._write(
            Panel(
                "\n".join(lines),
                title=f"[bold {COPPER}]Artifacts[/]",
                border_style=TEAL,
                padding=(1, 2),
            ),
        )

    def _inspect_workflow(self, query: str = "") -> None:
        lines = [
            f"[bold {AMBER}]task[/]: {escape(self.active_task)}",
            f"[bold {AMBER}]working[/]: {'yes' if self.busy else 'no'}",
            f"[bold {AMBER}]draft[/]: {len(self.draft_lines)} line(s)",
            f"[bold {AMBER}]pending confirmation[/]: {escape(self.pending_action.summary if self.pending_action else 'none')}",
            f"[bold {AMBER}]pending review[/]: {escape(self._pending_review_summary())}",
            "",
            f"[bold {AMBER}]authoring complete[/]: {self.latest_authoring_complete}",
            f"[bold {AMBER}]approved[/]: {self.latest_authoring_approved}",
            f"[bold {AMBER}]candidate validated[/]: {self.latest_candidate_validated}",
            f"[bold {AMBER}]synthesis converged[/]: {self.latest_synthesis_converged}",
            f"[bold {AMBER}]iterations[/]: {self.latest_synthesis_iterations if self.latest_synthesis_iterations is not None else '(unknown)'}",
            f"[bold {AMBER}]loss[/]: {self.latest_synthesis_loss if self.latest_synthesis_loss is not None else '(unknown)'}",
        ]
        if self.latest_status_summary:
            lines.extend(["", f"[bold {AMBER}]status[/]: {escape(self.latest_status_summary)}"])
        lines.extend(["", "[bold #f0c678]Artifacts[/]"])
        lines.extend(self._artifact_index_lines(include_discovered=True))
        query = query.strip()
        if query:
            matches = self._artifact_search_matches(query, max_matches=8)
            lines.extend(["", f"[bold #f0c678]Search: {escape(query)}[/]"])
            lines.extend(matches or [f"[dim {MUTED}]No matching artifact text found.[/]"])
        lines.extend([
            "",
            f"[dim {MUTED}]Use /schema, /policy, /artifacts, /export, /copy session, or /search QUERY.[/]",
        ])
        self._write(
            Panel(
                "\n".join(lines),
                title=f"[bold {COPPER}]Workflow inspection[/]",
                border_style=TEAL,
                padding=(1, 2),
            ),
        )

    def _search_artifacts(self, query: str = "") -> None:
        query = query.strip()
        if not query:
            lines = [
                "[bold #f0c678]Searchable workflow files[/]",
                *self._artifact_index_lines(include_discovered=True),
                "",
                f"[dim {MUTED}]Run /search QUERY to search schema, policy, eval logs, atoms, plans, and session files.[/]",
            ]
        else:
            matches = self._artifact_search_matches(query, max_matches=40)
            lines = [f"[bold #f0c678]Artifact search: {escape(query)}[/]"]
            lines.extend(matches or [f"[dim {MUTED}]No matching artifact text found.[/]"])
        self._write(
            Panel(
                "\n".join(lines),
                title=f"[bold {COPPER}]Artifact search[/]",
                border_style=TEAL,
                padding=(1, 2),
            ),
        )

    def _pending_review_summary(self) -> str:
        if self.pending_review is None:
            return "none"
        atom_name = getattr(self.pending_review.current, "name", "?")
        return f"{self.pending_review.stage_label}: {atom_name}"

    def _artifact_index_lines(self, *, include_discovered: bool = False) -> list[str]:
        rows: list[tuple[str, Path | None]] = [
            ("session", self.latest_session_dir),
            ("schema", self.latest_schema_path),
            ("policy", self.latest_policy_path),
        ]
        if include_discovered:
            for path in self._discover_artifact_files(limit=24):
                rows.append(("file", path))
        if not any(path for _, path in rows):
            return [f"[dim {MUTED}]No authoring artifacts are registered yet.[/]"]
        lines = []
        seen: set[Path] = set()
        for label, path in rows:
            if path is None:
                lines.append(f"[bold {AMBER}]{label}[/]: (not available)")
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            exists = "exists" if path.exists() else "missing"
            lines.append(f"[bold {AMBER}]{label}[/]: {escape(str(path))} [dim {MUTED}]({exists})[/]")
        return lines

    def _artifact_search_matches(self, query: str, *, max_matches: int) -> list[str]:
        needle = query.lower()
        matches: list[str] = []
        for path in self._discover_artifact_files(limit=80):
            if not path.exists() or not path.is_file() or not _is_searchable_artifact(path):
                continue
            try:
                text = path.read_text(errors="replace")
            except Exception:
                continue
            rel = _display_artifact_path(path, self.latest_session_dir)
            for lineno, line in enumerate(text.splitlines(), start=1):
                if needle in line.lower():
                    clipped = line.strip()
                    if len(clipped) > 180:
                        clipped = clipped[:177] + "..."
                    matches.append(
                        f"[bold {AMBER}]{escape(rel)}:{lineno}[/] {escape(clipped)}",
                    )
                    if len(matches) >= max_matches:
                        return matches
        return matches

    def _discover_artifact_files(self, *, limit: int) -> list[Path]:
        roots: list[Path] = []
        for path in (self.latest_schema_path, self.latest_policy_path):
            if path is not None:
                roots.append(path)
        if self.latest_session_dir is not None:
            roots.append(self.latest_session_dir)
        discovered: list[Path] = []
        seen: set[Path] = set()
        for root in roots:
            if root is None or not root.exists():
                continue
            candidates = [root] if root.is_file() else sorted(root.rglob("*"))
            for candidate in candidates:
                if not candidate.is_file() or not _is_searchable_artifact(candidate):
                    continue
                resolved = candidate.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                discovered.append(candidate)
                if len(discovered) >= limit:
                    return discovered
        return discovered

    def _show_schema_command(self, args: Sequence[str]) -> None:
        path = Path(args[0]) if args else self.latest_schema_path
        self._show_file_artifact(path, label="Cedar schema")

    def _show_policy_command(self, args: Sequence[str]) -> None:
        path = Path(args[0]) if args else self.latest_policy_path
        self._show_file_artifact(path, label="Cedar policy")

    def _show_file_artifact(self, path: Path | None, *, label: str) -> None:
        if path is None:
            command = "/schema" if "schema" in label.lower() else "/policy"
            self._write(
                f"[dim {MUTED}]No latest {label.lower()} is registered yet. "
                f"Run authoring first, or pass a file path: {command} PATH[/]",
            )
            return
        if not path.exists():
            self._write(f"[bold {RED}]{escape(label)} not found:[/] {escape(str(path))}")
            return
        text = path.read_text()
        self._write(
            Panel(
                Syntax(text, "cedar", word_wrap=True, theme="monokai"),
                title=f"[bold {COPPER}]{escape(label)}[/]",
                subtitle=f"[dim {MUTED}]{escape(str(path))}[/]",
                border_style=TEAL,
            ),
        )

    def _handle_copy_command(self, args: Sequence[str]) -> None:
        if not args:
            raise ValueError(
                "Use /copy last, /copy transcript, /copy session, /copy schema, "
                "/copy schema path, /copy policy, /copy policy path, or /copy draft.",
            )
        target = args[0].lower()
        mode = args[1].lower() if len(args) > 1 else "content"
        if target == "last":
            self._copy_text(self.last_assistant_text, label="last assistant message")
            return
        if target in {"transcript", "chat", "screen", "log"}:
            self._copy_text("\n".join(self.copyable_transcript), label="transcript")
            return
        if target == "session":
            if self.latest_session_dir is None:
                raise ValueError("No session path is available yet.")
            self._copy_text(str(self.latest_session_dir), label="session path")
            return
        if target == "draft":
            self._copy_text("\n".join(self.draft_lines), label="draft")
            return
        if target in {"schema", "policy"}:
            path = self.latest_schema_path if target == "schema" else self.latest_policy_path
            if path is None:
                raise ValueError(f"No latest {target} artifact is available yet.")
            if mode == "path":
                self._copy_text(str(path), label=f"{target} path")
                return
            if not path.exists():
                raise ValueError(f"{target} file not found: {path}")
            self._copy_text(path.read_text(), label=target)
            return
        if target in {"path", "text"}:
            value = " ".join(args[1:]).strip()
            if not value:
                raise ValueError(f"Use /copy {target} VALUE.")
            self._copy_text(value, label=target)
            return
        candidate = Path(args[0])
        if candidate.exists() and candidate.is_file():
            self._copy_text(candidate.read_text(), label=str(candidate))
            return
        self._copy_text(" ".join(args), label="text")

    def _export_artifacts(self, export_dir: Path | None = None) -> None:
        target_dir = export_dir or Path("autocedar-export")
        target_dir.mkdir(parents=True, exist_ok=True)

        copied: list[tuple[str, Path]] = []
        missing: list[str] = []

        def copy_artifact(label: str, source: Path | None, filename: str) -> None:
            if source is None:
                missing.append(label)
                return
            if not source.exists():
                missing.append(f"{label} ({source})")
                return
            destination = target_dir / filename
            shutil.copyfile(source, destination)
            copied.append((label, destination))

        copy_artifact("schema", self.latest_schema_path, "schema.cedarschema")
        copy_artifact("policy", self.latest_policy_path, "policy_store.cedar")

        transcript_path = target_dir / "transcript.txt"
        transcript_path.write_text("\n".join(self.copyable_transcript).strip() + "\n")
        copied.append(("transcript", transcript_path))

        artifacts_path = target_dir / "artifacts.txt"
        artifacts_path.write_text(
            "\n".join([
                f"session={self.latest_session_dir or ''}",
                f"schema={self.latest_schema_path or ''}",
                f"policy={self.latest_policy_path or ''}",
                f"authoring_complete={self.latest_authoring_complete}",
                f"approved={self.latest_authoring_approved}",
                f"candidate_validated={self.latest_candidate_validated}",
                f"synthesis_converged={self.latest_synthesis_converged}",
                f"synthesis_iterations={self.latest_synthesis_iterations or ''}",
                f"synthesis_loss={self.latest_synthesis_loss if self.latest_synthesis_loss is not None else ''}",
                f"status={self.latest_status_summary}",
                f"export={target_dir.resolve()}",
            ])
            + "\n",
        )
        copied.append(("artifact index", artifacts_path))

        lines = [f"[bold {GREEN}]Exported artifacts to:[/] {escape(str(target_dir.resolve()))}", ""]
        for label, path in copied:
            lines.append(f"[bold {AMBER}]{escape(label)}[/]: {escape(str(path))}")
        if missing:
            lines.extend(["", f"[dim {MUTED}]Missing: {escape(', '.join(missing))}[/]"])
        lines.extend([
            "",
            f"[dim {MUTED}]Open these files directly from your terminal/editor, or copy the folder path with /copy path {escape(str(target_dir.resolve()))}.[/]",
        ])
        self._write(
            Panel(
                "\n".join(lines),
                title=f"[bold {COPPER}]Export complete[/]",
                border_style=TEAL,
                padding=(1, 2),
            ),
        )

    def _copy_text(self, text: str, *, label: str) -> None:
        if not text:
            raise ValueError(f"Nothing to copy for {label}.")
        result = _copy_to_clipboard(text)
        if result.ok:
            self._say(f"Copied {label} to clipboard.")
            return
        self._write(
            Panel(
                escape(text),
                title=f"[bold {COPPER}]Copy fallback: {escape(label)}[/]",
                subtitle=f"[dim {MUTED}]{escape(result.message)}[/]",
                border_style=AMBER,
                padding=(1, 2),
            ),
        )

    def _save_draft(self, args: Sequence[str]) -> None:
        if not self.draft_lines:
            raise ValueError("Draft is empty; type prose first.")
        path = Path(args[0]) if args else DRAFT_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(self.draft_lines) + "\n")
        self._write(f"[bold {GREEN}]Saved draft to[/] {escape(str(path))}")
        if not self.busy and self.pending_review is None and self.pending_action is None:
            self.active_task = "idle"
            self._update_status()

    def _clear_draft(self) -> None:
        self.draft_lines.clear()
        self.drafting_active = False
        self.pending_action = None
        self.active_task = "idle"
        self.query_one(Input).placeholder = "Tell AutoCedar what to do, or type /help"
        self._say("I cleared the working policy draft.")
        self._update_status()

    def _start_drafting(self) -> None:
        self.drafting_active = True
        self.pending_action = None
        self.active_task = "idle"
        self.query_one(Input).placeholder = "Tell AutoCedar what to do, or type /help"
        self._say(
            "Policy authoring has started. Paste your natural-language requirements "
            "now; I’ll add those lines to the working draft.",
        )
        self._update_status()

    def _append_draft_text(self, raw: str) -> None:
        lines = _draft_lines_from_text(raw)
        if not lines:
            self._say("I didn’t find any non-empty requirement lines to add.")
            return
        self.draft_lines.extend(lines)
        label = "line" if len(lines) == 1 else "lines"
        self._say(
            f"I added {len(lines)} requirement {label} to the policy draft. "
            "When you’re ready, say “author this”, “save this as spec.md”, "
            "or “show the draft”.",
        )
        self._update_status()

    def _edit_draft(
        self,
        *,
        mode: str | None,
        line: int | None,
        value: str | None,
    ) -> None:
        if not self.draft_lines:
            self._say("The draft is empty. Start a policy draft and add requirements first.")
            return
        normalized_mode = (mode or "").strip().lower()
        if normalized_mode == "replace_all":
            lines = _draft_lines_from_text(value or "")
            if not lines:
                self._write(f"[bold {RED}]Replacement draft text cannot be empty.[/]")
                return
            self.draft_lines = lines
            self.drafting_active = True
            self._say(f"I replaced the working draft. It now has {len(lines)} line(s).")
            self._show_draft()
            self._update_status()
            return

        if line is None:
            self._write(f"[bold {RED}]Draft edit needs a 1-based line number.[/]")
            return
        index = line - 1
        if normalized_mode in {"set_line", "delete_line"} and not (0 <= index < len(self.draft_lines)):
            self._write(
                f"[bold {RED}]Line {line} does not exist.[/] "
                f"The draft has {len(self.draft_lines)} line(s).",
            )
            return
        if normalized_mode == "insert_line" and not (0 <= index <= len(self.draft_lines)):
            self._write(
                f"[bold {RED}]Insert position {line} is out of range.[/] "
                f"Use 1 through {len(self.draft_lines) + 1}.",
            )
            return

        if normalized_mode == "set_line":
            replacement = (value or "").strip()
            if not replacement:
                self._write(f"[bold {RED}]Replacement line cannot be empty.[/]")
                return
            old = self.draft_lines[index]
            self.draft_lines[index] = replacement
            self._say(f"I replaced draft line {line}.")
            self._write(f"[dim {MUTED}]old:[/] {escape(old)}")
            self._write(f"[dim {MUTED}]new:[/] {escape(replacement)}")
        elif normalized_mode == "delete_line":
            removed = self.draft_lines.pop(index)
            self._say(f"I deleted draft line {line}.")
            self._write(f"[dim {MUTED}]removed:[/] {escape(removed)}")
        elif normalized_mode == "insert_line":
            inserted = (value or "").strip()
            if not inserted:
                self._write(f"[bold {RED}]Inserted line cannot be empty.[/]")
                return
            self.draft_lines.insert(index, inserted)
            self.drafting_active = True
            self._say(f"I inserted a new draft line at {line}.")
            self._write(f"[dim {MUTED}]inserted:[/] {escape(inserted)}")
        else:
            self._write(
                f"[bold {RED}]Unsupported draft edit mode:[/] {escape(str(mode))}. "
                "Use set_line, delete_line, insert_line, or replace_all.",
            )
            return
        self._show_draft()
        self._update_status()

    def _start_author(self, options: AuthorOptions) -> None:
        self._start_task(
            f"author {options.spec}",
            lambda: self._author(options),
        )

    def _run_author_action(self, options: AuthorOptions, *, from_draft: bool) -> None:
        if from_draft:
            self._save_draft([str(options.spec)])
        self._start_author(options)

    def _start_task(self, name: str, func: Any) -> None:
        if self.busy:
            self._write(f"[{AMBER}]The agent is already running a task.[/]")
            return
        self.busy = True
        self.active_task = name
        self.query_one(Input).placeholder = "Working. Wait for the next prompt or atom review..."
        self._update_status()
        self._start_activity(f"{name} in progress")
        self._write(f"[bold {COPPER}]Starting:[/] {escape(name)}")
        self.run_worker(func, thread=True, exclusive=False, exit_on_error=False)

    def _make_anthropic_client(self) -> Any:
        import anthropic

        return anthropic.Anthropic(api_key=self._active_api_key())

    def _author(self, options: AuthorOptions) -> None:
        try:
            if not options.spec.exists():
                raise FileNotFoundError(f"spec not found: {options.spec}")
            llm = LLMClient(
                provider=self.llm_provider,
                model=options.model or self.llm_model,
                effort=options.effort or self.llm_effort,
            )

            spec_text = options.spec.read_text()

            def schema_proposer(text: str) -> list[Any]:
                self.call_from_thread(self._start_activity, "schema atomization")
                return propose_schema_atoms(text, llm)

            def property_proposer(
                text: str,
                schema_path: str,
                prior_atoms: list[Any],
                prior_decisions: list[Any],
            ) -> Any:
                self.call_from_thread(self._start_activity, "property atomization")
                return propose_property_atom(text, schema_path, llm, prior_atoms, prior_decisions)

            def schema_repairer(
                text: str,
                rejected_atom: Any,
                reason: str,
                prior_atoms: list[Any],
            ) -> Any:
                _ = prior_atoms
                self.call_from_thread(self._start_activity, "schema atom repair")
                return llm.propose_alternative_atom(rejected_atom, reason, text)

            def schema_fixer(schema_text: str, cedar_error: str, text: str) -> str:
                self.call_from_thread(self._start_activity, "schema validation repair")
                return llm.fix_schema(schema_text, cedar_error, text)

            def property_repairer(
                text: str,
                schema_path: str,
                rejected_atom: Any,
                reason: str,
                prior_atoms: list[Any],
            ) -> Any:
                self.call_from_thread(self._start_activity, "property repair")
                schema_text = Path(schema_path).read_text()
                return llm.propose_alternative_property_atom(
                    rejected_atom,
                    reason,
                    text,
                    schema_text,
                    prior_atoms,
                )

            reviewer = TuiAtomReviewer(self)

            def review_atom(atom: Any) -> Any:
                if options.auto_approve:
                    return auto_approve(atom)
                return reviewer(atom)

            review_atom.begin_stage = reviewer.begin_stage  # type: ignore[attr-defined]
            review_atom.end_stage = reviewer.end_stage  # type: ignore[attr-defined]
            review_atom.schema_ready = reviewer.schema_ready  # type: ignore[attr-defined]
            review_atom.property_plan_ready = reviewer.property_plan_ready  # type: ignore[attr-defined]
            review_atom.property_progress = reviewer.property_progress  # type: ignore[attr-defined]

            stage3_synthesizer = make_harness_synthesizer(
                phase1_model=options.model or self.llm_model,
                phase2_model=options.model or self.llm_model,
                no_review=True,
                quiet=True,
                output_callback=lambda text: self.call_from_thread(
                    self._write,
                    text,
                ),
            )

            def synthesize_with_status(scenario_dir: Path) -> Path:
                self.call_from_thread(self._start_activity, "synthesis iterations")
                return stage3_synthesizer(scenario_dir)

            result = author_pipeline(
                spec_path=options.spec,
                output_dir=options.out,
                session_id=options.session_id,
                review_atom=review_atom,
                propose_schema_atoms=schema_proposer,
                propose_property_atom=property_proposer,
                repair_schema_atom=schema_repairer,
                fix_schema=schema_fixer,
                repair_property_atom=property_repairer,
                synthesize=synthesize_with_status,
                schema_path_override=str(options.schema) if options.schema else None,
            )
            self.call_from_thread(
                self._register_authoring_artifacts,
                result.session_dir,
                result.candidate_path,
                schema_override=options.schema,
            )
            self.call_from_thread(
                self._record_authoring_result,
                result.final_user_approved,
            )
            lines = [
                f"[bold {GREEN}]Authoring complete.[/]",
                f"[bold {AMBER}]session[/]:   {escape(str(result.session_dir))}",
                f"[bold {AMBER}]schema[/]:    {escape(str(self.latest_schema_path or '(not available)'))}",
                f"[bold {AMBER}]policy[/]:    {escape(str(self.latest_policy_path or '(not available)'))}",
                f"[bold {AMBER}]approved[/]:  {result.final_user_approved}",
            ]
            if result.notes:
                lines.append("")
                lines.append("[bold]notes:[/]")
                lines.extend(f"  - {escape(note)}" for note in result.notes)
            lines.extend([
                "",
                "[bold]Useful commands:[/]",
                "  /schema              show generated schema",
                "  /policy              show generated policy",
                "  /artifacts           show all result paths",
                "  /export              write schema/policy/transcript to ./autocedar-export",
                "  /copy schema path    copy schema path",
                "  /copy policy path    copy policy path",
                "  /copy schema         copy schema text when clipboard is available",
                "  /copy policy         copy policy text when clipboard is available",
            ])
            self.call_from_thread(
                self._write,
                Panel(
                    "\n".join(lines),
                    title=f"[bold {COPPER}]Authoring result[/]",
                    border_style=GREEN,
                    padding=(1, 2),
                ),
            )
        except Exception as exc:
            self.call_from_thread(
                self._write,
                f"[bold {RED}]Authoring failed:[/] {escape(str(exc))}",
            )
        finally:
            self.call_from_thread(self._finish_task)

    def _register_authoring_artifacts(
        self,
        session_dir: Path,
        candidate_path: Path | None,
        *,
        schema_override: Path | None,
    ) -> None:
        self.latest_session_dir = session_dir
        final_schema = session_dir / "stage1" / "final_schema.cedarschema"
        if final_schema.exists():
            self.latest_schema_path = final_schema
        elif schema_override is not None:
            self.latest_schema_path = schema_override
        if candidate_path and candidate_path.exists():
            self.latest_policy_path = candidate_path
        else:
            scenario_candidate = session_dir / "scenario" / "candidate.cedar"
            self.latest_policy_path = scenario_candidate if scenario_candidate.exists() else None

    def _record_authoring_result(self, final_user_approved: bool) -> None:
        self.latest_authoring_complete = True
        self.latest_authoring_approved = final_user_approved
        summary = _read_latest_synthesis_summary(self.latest_session_dir, self.latest_policy_path)
        self.latest_candidate_validated = summary["validated"]
        self.latest_synthesis_converged = summary["converged"]
        self.latest_synthesis_iterations = summary["iterations"]
        self.latest_synthesis_loss = summary["loss"]
        self.latest_status_summary = summary["summary"]
        self._update_status()

    def _verify_workspace(self, workspace: Path) -> None:
        try:
            from autocedar.harness.orchestrator import run_verification

            if not workspace.exists():
                raise FileNotFoundError(f"workspace not found: {workspace}")
            candidate = workspace / "candidate.cedar"
            if not candidate.exists():
                raise FileNotFoundError(f"candidate not found: {candidate}")

            vr = run_verification(str(workspace))
            lines: list[str] = []
            for result in vr.results:
                status = "PASS" if result.passed else "FAIL"
                lines.append(f"{result.check_name}: {status} ({result.check_type})")
                if not result.passed and result.counterexample:
                    lines.append(result.counterexample)
            lines.append(f"loss: {vr.loss}")
            self.call_from_thread(self._write, "\n".join(lines))
        except Exception as exc:
            self.call_from_thread(
                self._write,
                f"[bold {RED}]Verification failed:[/] {escape(str(exc))}",
            )
        finally:
            self.call_from_thread(self._finish_task)

    def _synthesize(self, options: SynthesizeOptions) -> None:
        output = io.StringIO()
        try:
            from autocedar.harness.eval_harness import (
                DEFAULT_MODEL,
                DEFAULT_PHASE1_MODEL,
                MAX_ITERATIONS,
                run_scenario,
            )

            run_id = options.run_id or datetime.datetime.now(
                datetime.timezone.utc,
            ).strftime("%Y%m%dT%H%M%SZ")
            run_dir = options.out / run_id
            run_dir.mkdir(parents=True, exist_ok=True)

            phase1_model = options.phase1_model or self.llm_model or DEFAULT_PHASE1_MODEL
            phase2_model = options.phase2_model or self.llm_model or DEFAULT_MODEL
            max_iters = options.max_iters or MAX_ITERATIONS

            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                results = [
                    run_scenario(
                        scenario_path=os.path.abspath(scenario),
                        run_dir=str(run_dir),
                        phase1_model=phase1_model,
                        phase2_model=phase2_model,
                        max_iters=max_iters,
                        gen_references=options.gen_references,
                        no_review=options.no_review,
                    )
                    for scenario in options.scenarios
                ]

            if output.getvalue().strip():
                self.call_from_thread(self._write, output.getvalue().strip())
            summary = [f"[bold {GREEN}]Synthesis finished.[/]", f"output: {run_dir}"]
            for result in results:
                status = "PASS" if result.converged else "FAIL"
                if result.error:
                    status = "ERROR"
                summary.append(
                    f"{result.scenario}: {status} "
                    f"iters={result.iterations}/{result.max_iterations} "
                    f"loss={result.final_loss} "
                    f"cost=${result.estimated_cost_usd:.4f}",
                )
                if result.error:
                    summary.append(f"  {result.error}")
            self.call_from_thread(self._write, "\n".join(summary))
        except Exception as exc:
            captured = output.getvalue().strip()
            if captured:
                self.call_from_thread(self._write, captured)
            self.call_from_thread(
                self._write,
                f"[bold {RED}]Synthesis failed:[/] {escape(str(exc))}",
            )
        finally:
            self.call_from_thread(self._finish_task)

    def _finish_task(self) -> None:
        self.busy = False
        self._stop_activity()
        if self.pending_review is None:
            self.active_task = "idle"
            self.query_one(Input).placeholder = "Tell AutoCedar what to do, or type /help"
        self._update_status()

    def _render_review_request(self, request: ReviewRequest) -> None:
        atom = request.current
        if atom.__class__.__name__ == "PropertyAtom":
            text = render_property_atom(atom, request.index, request.total)
        else:
            text = render_schema_atom(atom, request.index, request.total or request.index)
        self._write(
            Panel(
                text,
                title=f"[bold {COPPER}]{escape(request.stage_label)}[/]",
                subtitle=f"[dim {MUTED}]A approve  E edit  S show[/]",
                border_style=COPPER,
                padding=(1, 2),
            ),
        )

    def _write(self, content: Any) -> None:
        self.query_one("#transcript", RichLog).write(content)

    def _say(self, text: str) -> None:
        self.last_assistant_text = _strip_rich_markup(text)
        self.copyable_transcript.append(f"autocedar > {self.last_assistant_text}")
        self._write(self._assistant_line(text))

    def _assistant_line(self, text: str) -> str:
        return f"[bold {AMBER}]autocedar[/] [dim {MUTED}]>[/] {text}"

    def _clear_stream_output(self) -> None:
        stream = self.query_one("#stream", Static)
        stream.update("")
        stream.display = False
        self.activity_message = ""

    def _start_activity(self, message: str) -> None:
        self.activity_message = message
        self.activity_frame = 0
        self._render_activity()

    def _stop_activity(self) -> None:
        self._clear_stream_output()

    def _tick_activity(self) -> None:
        if not self.activity_message:
            return
        self.activity_frame += 1
        self._render_activity()

    def _render_activity(self) -> None:
        if not self.activity_message:
            return
        frames = "|/-\\"
        frame = frames[self.activity_frame % len(frames)]
        stream = self.query_one("#stream", Static)
        stream.display = True
        stream.update(
            self._assistant_line(
                f"[bold {TEAL}]{frame}[/] "
                f"{escape(self.activity_message)} "
                f"[dim {MUTED}]waiting for next step...[/]",
            ),
        )

    def _show_command_palette(self, value: str) -> None:
        palette = self.query_one("#command_palette", Static)
        palette.update(_slash_command_palette_text(value))
        palette.display = True

    def _hide_command_palette(self) -> None:
        palette = self.query_one("#command_palette", Static)
        palette.update("")
        palette.display = False

    def _update_status(self) -> None:
        draft_state = f"{len(self.draft_lines)} line(s)"
        drafting_state = "active" if self.drafting_active else "off"
        review_state = "yes" if self.pending_review is not None else "no"
        action_state = "yes" if self.pending_action is not None else "no"
        if is_codex_provider(self.llm_provider):
            auth_label = "codex auth"
            key_state = "set" if codex_auth_available() else "not set"
        else:
            auth_label = "api key"
            key_state = "set" if is_real_anthropic_api_key(self._active_api_key()) else "not set"
        busy_color = AMBER if self.busy else TEAL
        drafting_color = GREEN if self.drafting_active else MUTED
        review_color = CORAL if self.pending_review is not None else MUTED
        action_color = AMBER if self.pending_action is not None else MUTED
        key_color = TEAL if key_state == "set" else CORAL
        result_state = self.latest_status_summary or "none"
        if len(result_state) > 72:
            result_state = result_state[:69] + "..."
        result_color = GREEN if self.latest_candidate_validated else MUTED
        text = (
            f"[bold {COPPER}]Session[/]\n\n"
            f"[dim {MUTED}]current task[/]\n[bold {CREAM}]{escape(self.active_task)}[/]\n\n"
            f"[dim {MUTED}]agent state[/]\n[bold {busy_color}]{'working' if self.busy else 'ready'}[/]\n\n"
            f"[dim {MUTED}]model[/]\n[bold {CREAM}]{escape(_short_model(self.llm_model))}[/]\n\n"
            f"[dim {MUTED}]effort[/]\n[bold {CREAM}]{escape(self.llm_effort)}[/]\n\n"
            f"[dim {MUTED}]{auth_label}[/]\n[bold {key_color}]{key_state}[/]\n\n"
            f"[dim {MUTED}]pending atom review[/]\n[bold {review_color}]{review_state}[/]\n\n"
            f"[dim {MUTED}]property progress[/]\n[bold {CREAM}]{escape(self.property_progress_summary)}[/]\n\n"
            f"[dim {MUTED}]pending yes/no[/]\n[bold {action_color}]{action_state}[/]\n\n"
            f"[dim {MUTED}]draft capture[/]\n[bold {drafting_color}]{drafting_state}[/]\n\n"
            f"[dim {MUTED}]draft lines[/]\n[bold {CREAM}]{draft_state}[/]\n\n"
            f"[dim {MUTED}]latest result[/]\n[bold {result_color}]{escape(result_state)}[/]\n\n"
            f"[dim {MUTED}]Ask what any label means.[/]"
            )
        self.query_one("#status_text", Static).update(text)

    def _state_snapshot(self, *, for_model: bool = False) -> str:
        pending_summary = self.pending_action.summary if self.pending_action else "none"
        review_summary = "none"
        if self.pending_review is not None:
            atom_name = getattr(self.pending_review.current, "name", "?")
            review_summary = f"atom {self.pending_review.sequence}: {atom_name}"
        lines = [
            f"task: {self.active_task}",
            f"working: {'yes' if self.busy else 'no'}",
            f"provider: {self.llm_provider}",
            f"model: {self.llm_model}",
            f"effort: {self.llm_effort}",
            f"api key: {'set' if is_real_anthropic_api_key(self._active_api_key()) else 'not set'}",
            f"codex auth: {'set' if codex_auth_available() else 'not set'}",
            f"latest session: {self.latest_session_dir or 'none'}",
            f"latest schema: {self.latest_schema_path or 'none'}",
            f"latest policy: {self.latest_policy_path or 'none'}",
            f"property progress: {self.property_progress_summary}",
            f"drafting: {'active' if self.drafting_active else 'off'}",
            f"draft lines: {len(self.draft_lines)}",
            f"pending confirmation: {pending_summary}",
            f"pending review: {review_summary}",
        ]
        if self.draft_lines:
            latest = self.draft_lines[-1]
            if len(latest) > 160:
                latest = latest[:157] + "..."
            lines.append(f"latest draft line: {latest}")
        if not for_model:
            lines.append(
                "authoring context: clean spec/schema inputs only; chat is for conversation.",
            )
        return "\n".join(lines)

    def _process_context(self) -> str:
        return "\n".join(
            [
                "AutoCedar uses one tool-action control plane: the model proposes a structured AgentAction, and the executor performs concrete actions such as draft capture, author, verify, synthesize, save, show, artifact inspection, clipboard copy, clear, quit, and slash shortcuts.",
                "Slash commands are shortcuts into the same AgentAction executor as natural language.",
                "All slash-command capabilities are available to the planner as tools. For workflow-status or generated-file questions, the planner should choose inspect_workflow or search_artifacts instead of answering from guesswork.",
                "Authoring from prose without a schema override: AutoCedar saves the prose spec, runs Stage 1 schema atomization, proposes entity/action/attribute/type-alias atoms, and sends each proposed schema atom through HITL review before composing the schema.",
                "Authoring with a schema path: AutoCedar uses that existing schema directly and skips Stage 1 schema atomization/review.",
                "Stage 2 property atoms: AutoCedar proposes bounded local bundles from the spec, validated schema, approved prior atoms, and review history; symbolically verifies each atom; and sends each atom through HITL review one by one.",
                "The authoring engine receives clean inputs: saved spec text, optional schema path, and HITL review decisions. The chat transcript is not passed into authoring.",
                "Runtime LLM settings are user-selectable inside the TUI through /settings, /provider, /models, /model, /effort, and /apikey. Anthropic uses ANTHROPIC_API_KEY; Codex uses local Codex OAuth from the Codex auth cache. The selected model is used for agent planning, authoring atomization, and default synthesis phase models unless an explicit command overrides it. Effort is used for planning and authoring atomization calls that support adaptive thinking.",
                "Artifact inspection commands: /artifacts lists latest session/schema/policy paths, /schema shows the latest or provided schema file, /policy shows the latest or provided Cedar policy, and /copy can copy the latest session path, schema text/path, policy text/path, draft, or literal text.",
            ],
        )

    def _tui_legend_context(self) -> str:
        return "\n".join(
            [
                "HITL means human-in-the-loop review: AutoCedar pauses for the user to approve, reject, edit, ask about, or inspect proposed atoms.",
                "symcc means Cedar symbolic checking: it verifies candidate/reference relationships and liveness properties.",
                "CEGIS means counterexample-guided inductive synthesis: the v1 harness iterates on policy candidates using verifier feedback.",
                "task is the current operation; state is ready/working; pending atom review means the app is waiting for A/R/E/Q/S/V; pending yes/no means the app is waiting for confirmation; draft capture means policy requirements are being appended to the working draft; draft lines is the current prose draft size.",
            ],
        )


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _agent_tool_catalog() -> list[dict[str, str]]:
    """Return the model-visible tool/action catalog.

    This intentionally mirrors the slash shortcuts. Natural language and slash
    commands must share the same executor surface.
    """

    return [
        {"action": "help", "slash": "/help", "description": "show help"},
        {"action": "start_draft", "slash": "/draft start", "description": "start requirement capture"},
        {"action": "append_requirements", "slash": "+ TEXT", "description": "append requirements to the current draft"},
        {"action": "edit_draft", "slash": "/draft edit|delete|insert", "description": "edit the working draft"},
        {"action": "show_draft", "slash": "/draft show", "description": "show the working draft"},
        {"action": "clear_draft", "slash": "/clear draft", "description": "clear the working draft"},
        {"action": "save_draft", "slash": "/save", "description": "save the current draft"},
        {"action": "author_current_draft", "slash": "/author", "description": "run HITL authoring from the current draft"},
        {"action": "author_spec", "slash": "/author SPEC", "description": "run HITL authoring from a spec file"},
        {"action": "verify_workspace", "slash": "/verify", "description": "verify a workspace"},
        {"action": "synthesize", "slash": "/synthesize", "description": "run the synthesis harness"},
        {"action": "show_artifacts", "slash": "/artifacts", "description": "show latest artifact paths"},
        {"action": "inspect_workflow", "slash": "/inspect", "description": "inspect workflow state and generated files"},
        {"action": "search_artifacts", "slash": "/search", "description": "search latest workflow/generated files"},
        {"action": "show_schema", "slash": "/schema", "description": "show latest or provided schema"},
        {"action": "show_policy", "slash": "/policy", "description": "show latest or provided policy"},
        {"action": "export_artifacts", "slash": "/export", "description": "export schema, policy, transcript, and artifact index"},
        {"action": "copy", "slash": "/copy", "description": "copy artifact paths/text or transcript text"},
        {"action": "show_settings", "slash": "/settings", "description": "show provider/model/auth settings"},
        {"action": "set_provider", "slash": "/provider", "description": "switch model provider"},
        {"action": "show_models", "slash": "/models", "description": "show models"},
        {"action": "set_model", "slash": "/model", "description": "set model"},
        {"action": "set_effort", "slash": "/effort", "description": "set reasoning effort"},
        {"action": "set_api_key_prompt", "slash": "/apikey", "description": "prompt for an API key"},
        {"action": "set_api_key", "slash": "/apikey KEY", "description": "save an API key"},
        {"action": "clear_api_key", "slash": "/apikey clear", "description": "clear the saved API key"},
        {"action": "api_key_status", "slash": "/apikey status", "description": "show API key status"},
        {"action": "setup", "slash": "/setup", "description": "show dependency setup steps"},
        {"action": "doctor", "slash": "/doctor", "description": "diagnose environment readiness"},
        {"action": "clear_transcript", "slash": "/clear transcript", "description": "clear transcript display"},
        {"action": "quit", "slash": "/quit", "description": "exit AutoCedar"},
        {"action": "answer_review", "slash": "A|R|Q|S|V", "description": "answer pending atom review"},
        {"action": "edit_atom", "slash": "E field=value", "description": "edit pending atom review"},
        {"action": "respond", "slash": "", "description": "answer conversationally when no tool is needed"},
    ]


def _is_searchable_artifact(path: Path) -> bool:
    return path.suffix.lower() in {
        ".cedar",
        ".cedarschema",
        ".json",
        ".jsonl",
        ".log",
        ".md",
        ".py",
        ".txt",
    }


def _display_artifact_path(path: Path, session_dir: Path | None) -> str:
    if session_dir is not None:
        with contextlib.suppress(ValueError):
            return str(path.relative_to(session_dir))
    return str(path)


def _describe_start_draft_action() -> str:
    return "\n".join([
        "I’m going to start policy drafting mode.",
        "After it starts, paste your natural-language requirements and I’ll add those to the working draft.",
        "Questions and operational requests will still stay conversational.",
    ])


def _describe_author_action(options: AuthorOptions, *, from_draft: bool) -> str:
    lines = [
        "I’m going to run HITL authoring.",
        f"spec: {options.spec}",
        f"output: {options.out}",
        f"model: {options.model or default_model_for_provider(default_provider())}",
        f"effort: {options.effort or DEFAULT_EFFORT}",
    ]
    if options.session_id:
        lines.append(f"session id: {options.session_id}")
    if options.schema:
        lines.append(f"schema override: {options.schema}")
        lines.append("schema path: use the supplied schema directly; skip Stage 1 schema atomization.")
    else:
        lines.append(
            "schema path: none supplied; propose schema atoms from the spec and pause for HITL review.",
        )
    lines.append(
        "properties: propose bounded local Stage 2 property bundles, then symbolically verify and review each atom one by one.",
    )
    if from_draft:
        lines.append(f"I’ll first save the current draft to {options.spec}.")
    if options.auto_approve:
        lines.append("review: auto-approve is enabled, so HITL prompts will be skipped.")
    else:
        lines.append("review: I’ll pause for A/R/E/Q/S/V atom review decisions.")
    return "\n".join(lines)


def _describe_synthesize_action(options: SynthesizeOptions) -> str:
    lines = [
        "I’m going to run the v1 CEGIS synthesis harness.",
        "scenarios: " + ", ".join(str(path) for path in options.scenarios),
        f"output: {options.out}",
    ]
    if options.run_id:
        lines.append(f"run id: {options.run_id}")
    if options.phase1_model:
        lines.append(f"phase1 model: {options.phase1_model}")
    if options.phase2_model:
        lines.append(f"phase2 model: {options.phase2_model}")
    if options.max_iters:
        lines.append(f"max iterations: {options.max_iters}")
    lines.append(f"reference generation: {'yes' if options.gen_references else 'no'}")
    lines.append(f"review gate: {'skipped' if options.no_review else 'enabled'}")
    return "\n".join(lines)


def _agent_action_from_author_options(
    options: AuthorOptions,
    *,
    from_draft: bool,
) -> AgentAction:
    return AgentAction(
        kind="author_current_draft" if from_draft else "author_spec",
        spec=str(options.spec),
        out=str(options.out),
        session_id=options.session_id,
        schema_path=str(options.schema) if options.schema else None,
        model=options.model,
        effort=options.effort,
        auto_approve=options.auto_approve,
    )


def _author_options_from_agent_action(action: AgentAction) -> AuthorOptions:
    if action.kind == "author_current_draft":
        spec = Path(action.spec or DRAFT_PATH)
    else:
        if not action.spec:
            raise ValueError("I need a spec path before authoring.")
        spec = Path(action.spec)
    return AuthorOptions(
        spec=spec,
        out=Path(action.out) if action.out else Path("autocedar-runs"),
        session_id=action.session_id,
        schema=Path(action.schema_path) if action.schema_path else None,
        model=action.model,
        effort=action.effort,
        auto_approve=action.auto_approve,
    )


def _agent_action_from_synthesize_options(options: SynthesizeOptions) -> AgentAction:
    return AgentAction(
        kind="synthesize",
        scenarios=[str(path) for path in options.scenarios],
        out=str(options.out),
        run_id=options.run_id,
        phase1_model=options.phase1_model,
        phase2_model=options.phase2_model,
        max_iters=options.max_iters,
        gen_references=options.gen_references,
        no_review=options.no_review,
    )


def _synthesize_options_from_agent_action(action: AgentAction) -> SynthesizeOptions:
    if not action.scenarios:
        raise ValueError("I need a scenario path before synthesis.")
    return SynthesizeOptions(
        scenarios=[Path(scenario) for scenario in action.scenarios],
        out=Path(action.out) if action.out else Path("eval_runs"),
        run_id=action.run_id,
        phase1_model=action.phase1_model,
        phase2_model=action.phase2_model,
        max_iters=action.max_iters,
        gen_references=action.gen_references,
        no_review=action.no_review,
    )


def tokenize(raw: str) -> list[str]:
    text = raw.strip()
    if text.startswith("/"):
        text = text[1:]
    return shlex.split(text)


def parse_author_args(args: Sequence[str]) -> AuthorOptions:
    if not args:
        raise ValueError("Usage: /author SPEC [--out DIR] [--schema PATH] [--model MODEL] [--effort high]")
    spec = Path(args[0])
    options = AuthorOptions(spec=spec)
    i = 1
    while i < len(args):
        token = args[i]
        if token == "--out":
            i += 1
            if i >= len(args):
                raise ValueError("--out requires a directory")
            options.out = Path(args[i])
        elif token == "--schema":
            i += 1
            if i >= len(args):
                raise ValueError("--schema requires a path")
            options.schema = Path(args[i])
        elif token == "--session-id":
            i += 1
            if i >= len(args):
                raise ValueError("--session-id requires a value")
            options.session_id = args[i]
        elif token == "--model":
            i += 1
            if i >= len(args):
                raise ValueError("--model requires a model name")
            options.model = args[i]
        elif token == "--effort":
            i += 1
            if i >= len(args):
                raise ValueError("--effort requires low, medium, high, or max")
            effort = _normalize_effort(args[i])
            if effort is None:
                raise ValueError("--effort must be one of: low, medium, high, max")
            options.effort = effort
        elif token == "--auto-approve":
            options.auto_approve = True
        else:
            raise ValueError(f"Unknown /author option: {token}")
        i += 1
    return options


def parse_synthesize_args(args: Sequence[str]) -> SynthesizeOptions:
    scenarios: list[Path] = []
    options = SynthesizeOptions(scenarios=scenarios)
    i = 0
    while i < len(args):
        token = args[i]
        if token == "--out":
            i += 1
            if i >= len(args):
                raise ValueError("--out requires a directory")
            options.out = Path(args[i])
        elif token == "--run-id":
            i += 1
            if i >= len(args):
                raise ValueError("--run-id requires a value")
            options.run_id = args[i]
        elif token == "--phase1-model":
            i += 1
            if i >= len(args):
                raise ValueError("--phase1-model requires a value")
            options.phase1_model = args[i]
        elif token == "--phase2-model":
            i += 1
            if i >= len(args):
                raise ValueError("--phase2-model requires a value")
            options.phase2_model = args[i]
        elif token == "--max-iters":
            i += 1
            if i >= len(args):
                raise ValueError("--max-iters requires a value")
            options.max_iters = int(args[i])
        elif token == "--gen-references":
            options.gen_references = True
        elif token == "--no-review":
            options.no_review = True
        elif token.startswith("--"):
            raise ValueError(f"Unknown /synthesize option: {token}")
        else:
            scenarios.append(Path(token))
        i += 1
    if not scenarios:
        raise ValueError("Usage: /synthesize SCENARIO... [--no-review]")
    return options


def _split_review_input(raw: str) -> tuple[str, str]:
    stripped = raw.strip()
    if not stripped:
        return "", ""
    lower = stripped.lower()
    aliases = {
        "approve": "A",
        "reject": "R",
        "edit": "E",
        "question": "Q",
        "show": "S",
        "patches": "V",
    }
    for alias, key in aliases.items():
        if lower == alias:
            return key, ""
        if lower.startswith(alias + " "):
            return key, stripped[len(alias):].strip()
    return stripped[:1].upper(), stripped[1:].strip()


def _schema_overview_text(schema_text: str) -> str:
    entities: list[tuple[str, list[str], str]] = []
    actions: list[tuple[str, str, str, list[str]]] = []
    lines = schema_text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        entity_match = re.match(r"entity\s+([A-Za-z_][A-Za-z0-9_:]*)", line)
        action_match = re.match(r"action\s+([A-Za-z_][A-Za-z0-9_:]*)\s+appliesTo", line)

        if entity_match:
            name = entity_match.group(1)
            meta = ""
            parent_match = re.search(r"\bin\s+\[([^\]]+)\]", line)
            enum_match = re.search(r"\benum\s+\[([^\]]+)\]", line)
            if parent_match:
                meta = f" in [{parent_match.group(1)}]"
            if enum_match:
                meta = f" enum [{enum_match.group(1)}]"
            attrs: list[str] = []
            if "{" in line:
                i += 1
                while i < len(lines) and lines[i].strip() != "};":
                    attr = _schema_attr_line(lines[i])
                    if attr:
                        attrs.append(attr)
                    i += 1
            entities.append((name, attrs, meta))
        elif action_match:
            name = action_match.group(1)
            principals = ""
            resources = ""
            context_attrs: list[str] = []
            i += 1
            in_context = False
            while i < len(lines) and lines[i].strip() != "};":
                stripped = lines[i].strip()
                principal_match = re.match(r"principal:\s*\[([^\]]*)\]", stripped)
                resource_match = re.match(r"resource:\s*\[([^\]]*)\]", stripped)
                if principal_match:
                    principals = principal_match.group(1)
                elif resource_match:
                    resources = resource_match.group(1)
                elif stripped.startswith("context:"):
                    in_context = True
                elif in_context and stripped.startswith("},"):
                    in_context = False
                elif in_context:
                    attr = _schema_attr_line(stripped)
                    if attr:
                        context_attrs.append(attr)
                i += 1
            actions.append((name, principals or "...", resources or "...", context_attrs))
        i += 1

    out = ["Entities"]
    if not entities:
        out.append("  (none)")
    for name, attrs, meta in entities:
        out.append(f"  {name}{meta}")
        for attr in attrs:
            out.append(f"    - {attr}")

    out.append("")
    out.append("Actions")
    if not actions:
        out.append("  (none)")
    for name, principals, resources, context_attrs in actions:
        out.append(f"  {name}: [{principals}] -> [{resources}]")
        if context_attrs:
            out.append("    context")
            for attr in context_attrs:
                out.append(f"      - {attr}")
    return "\n".join(out)


def _schema_attr_line(line: str) -> str:
    stripped = line.strip().rstrip(",")
    attr_match = re.match(r"([A-Za-z_][A-Za-z0-9_?]*):\s*(.+)$", stripped)
    if not attr_match:
        return ""
    return f"{attr_match.group(1)}: {attr_match.group(2)}"


def _property_overview_text(properties: list[Any]) -> str:
    if not properties:
        return "No approved property atoms."

    by_action: dict[str, list[Any]] = {}
    for atom in properties:
        by_action.setdefault(str(getattr(atom, "action", "(no action)")), []).append(atom)

    out: list[str] = []
    for action, atoms in by_action.items():
        out.append(f"{action}")
        for atom in atoms:
            kind = str(getattr(atom, "constraint_type", "property")).upper()
            principals = ", ".join(getattr(atom, "principal_types", []) or ["..."])
            resources = ", ".join(getattr(atom, "resource_types", []) or ["..."])
            summary = str(getattr(atom, "plain_english_summary", ""))
            out.append(f"  - {kind}: [{principals}] -> [{resources}]")
            if summary:
                out.append(f"    {summary}")
        out.append("")
    return "\n".join(out).rstrip()


def _codex_models_text(info: Any) -> str:
    lines = [
        f"[dim {MUTED}]provider[/]\n[bold {CREAM}]openai-codex[/]",
        f"[dim {MUTED}]auth source[/]\n[bold {CREAM}]{escape(info.auth_source)}[/]",
        f"[dim {MUTED}]base url[/]\n[bold {CREAM}]{escape(info.base_url)}[/]",
        f"[dim {MUTED}]selectable thinking[/]\n[bold {CREAM}]{', '.join(info.thinking_efforts)}[/]",
        "",
        f"[bold {AMBER}]Visible models[/]",
    ]
    details = list(getattr(info, "model_details", []) or [])
    if not details:
        details = [type("_Model", (), {"slug": model})() for model in getattr(info, "models", [])]
    for detail in details:
        slug = str(getattr(detail, "slug", ""))
        display_name = str(getattr(detail, "display_name", "") or "")
        heading = slug if not display_name or display_name == slug else f"{slug} ({display_name})"
        lines.append(f"- [bold {CREAM}]{escape(heading)}[/]")
        reason = _format_reasoning_levels(detail)
        if reason:
            default_reasoning = str(getattr(detail, "default_reasoning_level", "") or "")
            suffix = f"; default {default_reasoning}" if default_reasoning else ""
            lines.append(f"  reasoning: {escape(reason)}{escape(suffix)}")
        context = _format_context_window(detail)
        if context:
            lines.append(f"  context: {escape(context)}")
        tiers = _join_nonempty(getattr(detail, "service_tiers", ()))
        speed = _join_nonempty(getattr(detail, "speed_tiers", ()))
        if tiers or speed:
            lines.append(f"  tiers: {escape(tiers or 'standard')}; speed: {escape(speed or 'standard')}")
        verbosity = str(getattr(detail, "default_verbosity", "") or "")
        if getattr(detail, "support_verbosity", False) or verbosity:
            lines.append(f"  verbosity: {escape(verbosity or 'supported')}")
        if getattr(detail, "supports_reasoning_summaries", False):
            lines.append("  summaries: reasoning summaries supported")
    lines.extend([
        "",
        f"[dim {MUTED}]Use /model MODEL and /effort low|medium|high|max. "
        "For Codex, /effort max sends the token-visible xhigh reasoning level.[/]",
    ])
    return "\n".join(lines)


def _format_reasoning_levels(detail: Any) -> str:
    levels = getattr(detail, "supported_reasoning_levels", ()) or ()
    if not levels:
        return ""
    out = []
    for item in levels:
        if not isinstance(item, tuple) or not item:
            continue
        effort = str(item[0])
        label = "max" if effort == "xhigh" else effort
        description = str(item[1]) if len(item) > 1 else ""
        if description:
            out.append(f"{label} ({description})")
        else:
            out.append(label)
    return "; ".join(out)


def _format_context_window(detail: Any) -> str:
    context = getattr(detail, "context_window", None)
    max_context = getattr(detail, "max_context_window", None)
    if context is None and max_context is None:
        return ""
    if context == max_context or max_context is None:
        return _format_int(context)
    return f"{_format_int(context)} default, {_format_int(max_context)} max"


def _format_int(value: Any) -> str:
    return f"{value:,}" if isinstance(value, int) else "unknown"


def _join_nonempty(values: Any) -> str:
    if not values:
        return ""
    return ", ".join(str(value) for value in values if str(value).strip())


def _render_cedar_for_review(atom: Any) -> str:
    if atom.__class__.__name__ == "PropertyAtom":
        return render_property_reference(atom)
    return render_schema_declaration(atom)


def _initial_model() -> str:
    return (
        os.environ.get("AUTOCEDAR_MODEL")
        or os.environ.get("AUTOCEDAR_AUTHOR_MODEL")
        or os.environ.get("AUTOCEDAR_CHAT_MODEL")
        or default_model_for_provider(default_provider())
    )


def _normalize_effort(effort: str | None) -> str | None:
    if effort is None:
        return None
    normalized = effort.strip().lower()
    if normalized in {"xhigh", "extra-high", "extra_high"}:
        return "max"
    return normalized if normalized in EFFORT_LEVELS else None


def _strip_wrapping_quotes(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1]
    return stripped


def _mask_api_key(value: str | None) -> str:
    if not value:
        return "not set"
    if len(value) <= 12:
        return value[:3] + "..."
    return f"{value[:7]}...{value[-4:]}"


def _slash_command_palette_text(value: str) -> str:
    matches = _slash_command_matches(value)
    if not matches:
        return (
            f"[bold {COPPER}]Slash commands[/]\n"
            f"[dim {MUTED}]No shortcut matches {escape(value)}. Type /help for the full command list.[/]"
        )
    lines = [f"[bold {COPPER}]Slash commands[/] [dim {MUTED}]Tab completes, Enter runs[/]"]
    for command, description in matches[:10]:
        lines.append(f"[bold {AMBER}]{command:<12}[/] [dim {MUTED}]{escape(description)}[/]")
    if len(matches) > 10:
        lines.append(f"[dim {MUTED}]+ {len(matches) - 10} more; keep typing to narrow.[/]")
    return "\n".join(lines)


def _slash_command_completion(value: str) -> str | None:
    if not value.startswith("/"):
        return None
    matches = _slash_command_matches(value)
    if not matches:
        return None
    command = matches[0][0]
    if value == command or value.startswith(command + " "):
        return None
    return command + " "


def _slash_command_matches(value: str) -> list[tuple[str, str]]:
    query = value.strip().lower()
    if not query.startswith("/"):
        return []
    matches = [
        (command, description)
        for command, description in SLASH_COMMAND_DESCRIPTIONS.items()
        if command.startswith(query)
    ]
    if not matches:
        needle = query.lstrip("/")
        matches = [
            (command, description)
            for command, description in SLASH_COMMAND_DESCRIPTIONS.items()
            if needle in command.lstrip("/") or needle in description.lower()
        ]
    return matches


def _copy_to_clipboard(text: str) -> ClipboardResult:
    commands = [
        (["pbcopy"], "pbcopy"),
        (["wl-copy"], "wl-copy"),
        (["xclip", "-selection", "clipboard"], "xclip"),
        (["xsel", "--clipboard", "--input"], "xsel"),
        (["clip.exe"], "clip.exe"),
    ]
    for cmd, label in commands:
        if shutil.which(cmd[0]) is None:
            continue
        try:
            subprocess.run(
                cmd,
                input=text,
                text=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            return ClipboardResult(True, f"copied with {label}")
        except Exception:
            continue
    return ClipboardResult(
        False,
        "No supported clipboard command was available, so the text is shown here for manual selection.",
    )


def _read_latest_synthesis_summary(
    session_dir: Path | None,
    policy_path: Path | None,
) -> dict[str, Any]:
    if session_dir is None:
        return {
            "validated": None,
            "converged": None,
            "iterations": None,
            "loss": None,
            "summary": "No authoring session is registered.",
        }
    log_candidates = [
        session_dir / "harness_runs" / "scenario" / "eval_log.json",
        session_dir / "scenario" / "eval_log.json",
    ]
    log_path = next((path for path in log_candidates if path.exists()), None)
    policy_exists = bool(policy_path and policy_path.exists())
    if log_path is None:
        return {
            "validated": None,
            "converged": None,
            "iterations": None,
            "loss": None,
            "summary": (
                "Policy file exists, but no Stage 3 eval_log.json was found."
                if policy_exists
                else "No generated policy file or Stage 3 eval_log.json is registered."
            ),
        }
    try:
        data = json.loads(log_path.read_text())
    except Exception as exc:
        return {
            "validated": None,
            "converged": None,
            "iterations": None,
            "loss": None,
            "summary": f"Could not read Stage 3 eval log: {exc}",
        }
    converged = bool(data.get("converged"))
    iterations = data.get("iterations")
    loss = data.get("final_loss")
    checks_total = data.get("checks_total")
    error = str(data.get("error") or "").strip()
    validated = bool(policy_exists and converged and loss == 0)
    if validated:
        summary = (
            f"Candidate passed all {checks_total} recorded checks"
            if checks_total is not None
            else "Candidate passed all recorded checks"
        )
        if iterations is not None:
            summary += f" in {iterations} iteration(s)"
        summary += "."
    elif error:
        summary = f"Stage 3 did not validate the candidate: {error}"
    elif loss is not None:
        summary = f"Stage 3 finished with loss={loss}; candidate is not fully validated."
    else:
        summary = "Stage 3 eval log exists, but validation status is unclear."
    return {
        "validated": validated,
        "converged": converged,
        "iterations": iterations if isinstance(iterations, int) else None,
        "loss": loss if isinstance(loss, int) else None,
        "summary": summary,
    }


def _redact_sensitive_input(raw: str) -> str:
    redacted = re.sub(
        r"\bANTHROPIC_API_KEY\s*=\s*[^\s]+",
        "ANTHROPIC_API_KEY=[redacted]",
        raw,
        flags=re.IGNORECASE,
    )
    redacted = re.sub(r"\bsk-ant-[A-Za-z0-9_\-.]+", "[redacted-api-key]", redacted)
    if redacted.strip().lower().startswith(("/apikey ", "/api-key ")):
        command = redacted.strip().split(maxsplit=1)[0]
        return f"{command} [redacted-api-key]"
    return redacted


def _strip_rich_markup(text: str) -> str:
    return re.sub(r"\[/?[^\]]+\]", "", text)


def _draft_lines_from_text(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _numbered_draft_text(lines: Sequence[str]) -> str:
    width = len(str(len(lines)))
    return "\n".join(f"{index:>{width}}. {line}" for index, line in enumerate(lines, start=1))


def _parse_line_number(value: str) -> int:
    try:
        line = int(value)
    except ValueError as exc:
        raise ValueError(f"Line number must be an integer, got {value!r}.") from exc
    if line < 1:
        raise ValueError("Line number must be 1 or greater.")
    return line


def _short_model(model: str) -> str:
    if len(model) <= 30:
        return model
    return model[:27] + "..."


def run_tui() -> int:
    load_dotenv()
    AutoCedarApp().run()
    return 0


def _agent_failure_message(exc: Exception) -> str:
    if is_anthropic_auth_error(exc):
        return (
            "Anthropic rejected the saved API key, so I cleared it from this "
            "session and the AutoCedar user config. Run /apikey again with the "
            "full key from the Anthropic console."
        )
    return (
        "The agent planner failed before any tool ran. I did not execute or "
        f"mutate anything. Error: {exc.__class__.__name__}: {escape(str(exc))}"
    )
