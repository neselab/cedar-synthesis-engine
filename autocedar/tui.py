"""Interactive Textual shell for AutoCedar."""

from __future__ import annotations

import contextlib
import datetime
import io
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
from autocedar.property_atomizer import propose_property_atoms
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
_COMMON_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "author",
    "build",
    "can",
    "check",
    "create",
    "draft",
    "for",
    "from",
    "generate",
    "it",
    "me",
    "no",
    "of",
    "please",
    "policy",
    "run",
    "save",
    "schema",
    "show",
    "synthesize",
    "that",
    "the",
    "this",
    "to",
    "verify",
    "with",
    "workspace",
}

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
    "help",
    "model",
    "new",
    "policy",
    "quit",
    "save",
    "schema",
    "settings",
    "setup",
    "synthesize",
    "verify",
}

SLASH_COMMAND_DESCRIPTIONS = {
    "/author": "run HITL authoring for a spec",
    "/verify": "verify a workspace",
    "/synthesize": "run the synthesis harness",
    "/setup": "show Cedar/CVC5 install steps",
    "/doctor": "check API key and verifier setup",
    "/settings": "show model, effort, and API-key status",
    "/model": "set the default LLM model",
    "/effort": "set low, medium, high, or max effort",
    "/apikey": "set or clear the API key for this session",
    "/draft": "show, start, or clear draft capture",
    "/artifacts": "show latest session/schema/policy paths",
    "/schema": "show latest or provided Cedar schema",
    "/policy": "show latest or provided Cedar policy",
    "/copy": "copy text or artifact paths",
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

  [#f0c678]/author SPEC[/] [--out DIR] [--session-id ID] [--schema PATH] [--model MODEL] [--effort high]
  [#f0c678]/verify[/] [WORKSPACE]
  [#f0c678]/synthesize SCENARIO...[/] [--out DIR] [--max-iters N] [--no-review]
  [#f0c678]/setup[/]                 show local Cedar/CVC5 install steps
  [#f0c678]/doctor[/]                check API-key, Cedar SymCC, and CVC5 setup
  [#f0c678]/settings[/]              show model, effort, and API key status
  [#f0c678]/model MODEL[/]           set the default LLM model
  [#f0c678]/effort low|medium|high|max[/]
  [#f0c678]/apikey[/] [KEY|clear]    set or clear ANTHROPIC_API_KEY for this session
  [#f0c678]/draft[/] [show|start|clear] show, start, or clear draft capture
  [#f0c678]/artifacts[/]             show latest session/schema/policy paths
  [#f0c678]/schema[/] [PATH]         show latest or provided Cedar schema
  [#f0c678]/policy[/] [PATH]         show latest or provided Cedar policy
  [#f0c678]/copy[/] last|transcript|session|schema|policy|draft [path] copy text or artifact path
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
[#f0c678]/model[/] claude-opus-4-7
[#f0c678]/effort[/] high
[#f0c678]/apikey[/]
[#f0c678]/draft[/]
[#f0c678]/artifacts[/]
[#f0c678]/schema[/]
[#f0c678]/policy[/]
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
class NaturalLanguageIntent:
    kind: str
    message: str = ""
    path: Path | None = None
    workspace: Path | None = None
    author_options: AuthorOptions | None = None
    synthesize_options: SynthesizeOptions | None = None
    settings_update: "SettingsUpdate | None" = None
    from_draft: bool = False


@dataclass
class SettingsUpdate:
    show: bool = False
    model: str | None = None
    effort: str | None = None
    api_key: str | None = None
    clear_api_key: bool = False
    prompt_api_key: bool = False


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

    def begin_stage(self, label: str, total: int) -> None:
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

    def __call__(self, atom: Any) -> ReviewedAtom:
        self.sequence += 1
        stage_label = self.stage_label
        if self.stage_total is None:
            index = self.sequence
            total = None
        else:
            self.stage_index += 1
            if self.stage_index > self.stage_total:
                index = self.stage_index - self.stage_total
                total = None
                stage_label = f"{self.stage_label} replacement"
                self.app.call_from_thread(
                    self.app._say,
                    "Reviewing a replacement property atom proposed after rejection.",
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
        self.chat_history: list[tuple[str, str]] = []
        self.llm_provider = default_provider()
        self.llm_model = _initial_model()
        self.llm_effort = _normalize_effort(os.environ.get("AUTOCEDAR_EFFORT")) or DEFAULT_EFFORT
        self.busy = False
        self.active_task = "idle"
        self.latest_session_dir: Path | None = None
        self.latest_schema_path: Path | None = None
        self.latest_policy_path: Path | None = None
        self.copyable_transcript: list[str] = []
        self.last_assistant_text = ""

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
        self._handle_shell_input(raw)

    def begin_review(self, request: ReviewRequest) -> None:
        self.pending_review = request
        self.active_task = request.stage_label.lower()
        self.query_one(Input).placeholder = "Review: A, R reason, E field=value, Q question, S, V"
        self._write(f"[bold {AMBER}]Review required before the agent continues.[/]")
        self._render_review_request(request)
        self._update_status()

    def begin_review_stage(self, label: str, total: int) -> None:
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
                    "Examples: E cedar_type=Bool, E optional=true, E action=view.",
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

    def _handle_shell_input(self, raw: str) -> None:
        stripped = raw.strip()
        if stripped.startswith("+"):
            self._handle_explicit_draft_line(stripped[1:].strip())
            return
        if not raw.startswith("/"):
            lowered = _squash(raw).lower().rstrip("?.!")
            if lowered in {"show schema", "show the schema", "show me the schema"}:
                self._show_schema_command([])
                return
            if lowered in {
                "show policy",
                "show the policy",
                "show me the policy",
                "show policies",
                "show the policies",
                "show cedar policy",
                "show the cedar policy",
            }:
                self._show_policy_command([])
                return
            if lowered in {
                "show artifacts",
                "show the artifacts",
                "show paths",
                "show the paths",
                "where are the artifacts",
            }:
                self._show_artifacts()
                return
            if lowered in {
                "copy session",
                "copy session path",
                "copy the session path",
                "copy session link",
                "copy the session link",
                "copy session directory",
                "copy the session directory",
            }:
                self._handle_copy_command(["session"])
                return
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
        lowered = _squash(raw).lower()
        if self.drafting_active and lowered in {"clear it", "wipe it", "reset it", "delete it"}:
            self._request_confirmation(
                "I’m going to clear the working policy draft.",
                self._clear_draft,
            )
            return
        intent = interpret_natural_language(raw, has_draft=bool(self.draft_lines))
        if (
            self.drafting_active
            and intent.kind == "message"
            and _looks_like_active_draft_statement(raw)
        ):
            self._append_draft_text(raw)
            return
        try:
            if intent.kind == "help":
                self._say(HELP_TEXT)
            elif intent.kind == "settings":
                if intent.settings_update is None:
                    self._show_settings()
                else:
                    self._apply_settings_update(intent.settings_update)
            elif intent.kind == "quit":
                self._say("I’ll close the session.")
                self.exit()
            elif intent.kind == "clear_transcript":
                self.action_clear_log()
            elif intent.kind == "clear_draft":
                self._request_confirmation(
                    "I’m going to clear the working policy draft.",
                    self._clear_draft,
                )
            elif intent.kind == "start_draft":
                if self.drafting_active:
                    self._say(
                        "Drafting is already active. Policy requirements you give me "
                        "will be added to the working draft.",
                    )
                else:
                    self._request_confirmation(
                        _describe_start_draft_action(),
                        self._start_drafting,
                    )
            elif intent.kind == "show_draft":
                self._show_draft()
            elif intent.kind == "save_draft":
                args = [str(intent.path)] if intent.path else []
                path = Path(args[0]) if args else DRAFT_PATH
                self._request_confirmation(
                    f"I’m going to save the current draft to {path}.",
                    lambda args=args: self._save_draft(args),
                )
            elif intent.kind == "verify":
                workspace = intent.workspace or Path("workspace")
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
            elif intent.kind == "author":
                options = intent.author_options
                if options is None:
                    raise ValueError("I need a spec path or a draft before authoring.")
                options = self._resolve_author_options(options)
                self._request_confirmation(
                    _describe_author_action(options, from_draft=intent.from_draft),
                    lambda options=options, intent=intent: self._run_author_action(
                        options,
                        from_draft=intent.from_draft,
                    ),
                )
            elif intent.kind == "synthesize":
                options = intent.synthesize_options
                if options is None:
                    raise ValueError("I need a scenario path before synthesis.")
                options = self._resolve_synthesize_options(options)
                self._request_confirmation(
                    _describe_synthesize_action(options),
                    lambda options=options: self._start_task(
                        "synthesize",
                        lambda: self._synthesize(options),
                    ),
                )
            elif intent.kind == "append_draft":
                if self.drafting_active:
                    self._append_draft_text(raw)
                else:
                    self._request_confirmation(
                        _describe_start_draft_action(),
                        self._start_drafting,
                    )
            else:
                self._start_chat_response(
                    raw,
                    fallback=intent.message or "I’m not sure what to do with that yet.",
                )
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
            if command == "help":
                self._write(HELP_TEXT)
            elif command == "clear":
                self._handle_clear_command(args)
            elif command == "settings":
                self._show_settings()
            elif command == "setup":
                self._show_setup_plan()
            elif command == "doctor":
                self._show_doctor_report()
            elif command == "model":
                self._handle_model_command(args)
            elif command == "effort":
                self._handle_effort_command(args)
            elif command in {"apikey", "api-key"}:
                self._handle_api_key_command(args)
            elif command == "new":
                self._request_confirmation(
                    "I’m going to clear the working policy draft.",
                    self._clear_draft,
                )
            elif command == "draft":
                self._handle_draft_command(args)
            elif command == "artifacts":
                self._show_artifacts()
            elif command == "schema":
                self._show_schema_command(args)
            elif command == "policy":
                self._show_policy_command(args)
            elif command == "copy":
                self._handle_copy_command(args)
            elif command == "save":
                path = Path(args[0]) if args else DRAFT_PATH
                self._request_confirmation(
                    f"I’m going to save the current draft to {path}.",
                    lambda args=args: self._save_draft(args),
                )
            elif command in {"quit", "exit"}:
                self.exit()
            elif command == "verify":
                workspace = Path(args[0]) if args else Path("workspace")
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
            elif command == "author":
                options = self._resolve_author_options(parse_author_args(args))
                self._request_confirmation(
                    _describe_author_action(options, from_draft=False),
                    lambda options=options: self._run_author_action(options, from_draft=False),
                )
            elif command == "synthesize":
                options = self._resolve_synthesize_options(parse_synthesize_args(args))
                self._request_confirmation(
                    _describe_synthesize_action(options),
                    lambda options=options: self._start_task(
                        "synthesize",
                        lambda: self._synthesize(options),
                    ),
                )
        except ValueError as exc:
            self._write(f"[bold {RED}]{escape(str(exc))}[/]")

    def _handle_explicit_draft_line(self, line: str) -> None:
        if not line:
            self._write(f"[bold {RED}]Use + followed by the requirement text.[/]")
            return
        if not self.drafting_active:
            self.drafting_active = True
        self._append_draft_text(line)

    def _handle_clear_command(self, args: Sequence[str]) -> None:
        target = args[0].lower() if args else "transcript"
        if target in {"draft", "spec", "policy"}:
            self._request_confirmation(
                "I’m going to clear the working policy draft.",
                self._clear_draft,
            )
            return
        if target in {"transcript", "screen", "chat", "log"}:
            self.action_clear_log()
            return
        raise ValueError("Use /clear transcript or /clear draft.")

    def _handle_draft_command(self, args: Sequence[str]) -> None:
        target = args[0].lower() if args else ""
        if target in {"clear", "reset", "wipe", "new"}:
            self._request_confirmation(
                "I’m going to clear the working policy draft.",
                self._clear_draft,
            )
            return
        if target in {"start", "capture", "begin"}:
            if self.drafting_active:
                self._say(
                    "Drafting is already active. Send policy requirements and I’ll "
                    "add them to the working draft.",
                )
            else:
                self._start_drafting()
            return
        if target in {"show", "view", ""}:
            if not self.drafting_active and not self.draft_lines and target == "":
                self._start_drafting()
            else:
                self._show_draft()
            return
        raise ValueError("Use /draft, /draft show, /draft start, or /draft clear.")

    def _handle_model_command(self, args: Sequence[str]) -> None:
        if not args:
            self._show_settings()
            return
        self._set_model(args[0])

    def _handle_effort_command(self, args: Sequence[str]) -> None:
        if not args:
            self._show_settings()
            return
        self._set_effort(args[0])

    def _handle_api_key_command(self, args: Sequence[str]) -> None:
        if not args:
            self.pending_secret = "api_key"
            self.query_one(Input).placeholder = "Paste ANTHROPIC_API_KEY, or type cancel"
            self._say(
                "Paste your Anthropic API key. I’ll redact it in the transcript "
                "and save it to the user-level AutoCedar config. Type “cancel” to stop.",
            )
            self._update_status()
            return
        value = args[0]
        if value.lower() in {"clear", "unset", "remove", "delete"}:
            self._clear_api_key()
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

    def _apply_settings_update(self, update: SettingsUpdate) -> None:
        changed = False
        if update.clear_api_key:
            self._clear_api_key()
            changed = True
        if update.api_key:
            self._set_api_key(update.api_key)
            changed = True
        if update.prompt_api_key:
            self._handle_api_key_command([])
            changed = True
        if update.model:
            self._set_model(update.model)
            changed = True
        if update.effort:
            self._set_effort(update.effort)
            changed = True
        if update.show or not changed:
            self._show_settings()

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
        value = _strip_wrapping_quotes(api_key.strip())
        if not value:
            raise ValueError("API key cannot be empty.")
        path = write_user_config_value(ANTHROPIC_API_KEY, value)
        self._say(
            "Anthropic API key saved "
            f"([dim {MUTED}]{escape(_mask_api_key(value))}[/]) to "
            f"[dim {MUTED}]{escape(str(path))}[/].",
        )
        self._update_status()

    def _clear_api_key(self) -> None:
        path = remove_user_config_value(ANTHROPIC_API_KEY)
        self._say(f"Anthropic API key removed from [dim {MUTED}]{escape(str(path))}[/].")
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
        api_key = os.environ.get(ANTHROPIC_API_KEY)
        api_key_is_real = is_real_anthropic_api_key(api_key)
        codex_auth = "uses local Codex login" if self.llm_provider in {"codex", "openai-codex"} else ""
        return "\n".join(
            [
                f"[dim {MUTED}]provider[/]\n[bold {CREAM}]{escape(self.llm_provider)}[/]",
                f"[dim {MUTED}]model[/]\n[bold {CREAM}]{escape(self.llm_model)}[/]",
                f"[dim {MUTED}]effort[/]\n[bold {CREAM}]{escape(self.llm_effort)}[/]",
                (
                    f"[dim {MUTED}]api key[/]\n[bold {TEAL}]set[/] "
                    f"[dim {MUTED}]({_mask_api_key(api_key)})[/]"
                    if api_key_is_real
                    else f"[dim {MUTED}]api key[/]\n[bold {TEAL}]{codex_auth}[/]"
                    if codex_auth
                    else f"[dim {MUTED}]api key[/]\n[bold {CORAL}]not set[/]"
                ),
                "",
                f"[dim {MUTED}]Use /model, /effort, or /apikey to change these.[/]",
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
                "\n".join(self.draft_lines),
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
        lines.extend([
            "",
            f"[dim {MUTED}]Use /schema, /policy, /copy session, /copy schema path, or /copy policy path.[/]",
        ])
        self._write(
            Panel(
                "\n".join(lines),
                title=f"[bold {COPPER}]Artifacts[/]",
                border_style=TEAL,
                padding=(1, 2),
            ),
        )

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
        self._update_status()
        self._write(f"[bold {COPPER}]Starting:[/] {escape(name)}")
        self.run_worker(func, thread=True, exclusive=False, exit_on_error=False)

    def _start_chat_response(self, raw: str, *, fallback: str) -> None:
        if self.busy:
            self._say(fallback)
            return
        self.busy = True
        self.active_task = "thinking"
        self._update_status()
        self.run_worker(
            lambda: self._answer_chat(raw, fallback=fallback),
            thread=True,
            exclusive=False,
            exit_on_error=False,
        )

    def _answer_chat(self, raw: str, *, fallback: str) -> None:
        try:
            if is_real_anthropic_api_key(os.environ.get(ANTHROPIC_API_KEY)):
                answer = self._stream_chat_model(raw)
            else:
                answer = self._local_chat_response(raw, fallback=fallback)
                self.call_from_thread(self._say, answer)
            self.chat_history.append((raw, answer))
            self.chat_history = self.chat_history[-8:]
        except Exception as exc:
            self.call_from_thread(self._clear_stream_output)
            self.call_from_thread(self._say, _chat_failure_message(exc))
        finally:
            self.call_from_thread(self._finish_task)

    def _local_chat_response(self, raw: str, *, fallback: str) -> str:
        lowered = _squash(raw).lower().rstrip("?!.")
        if "llm" in lowered or "language model" in lowered or "ai" in lowered:
            if self.llm_provider in {"codex", "openai-codex"}:
                return (
                    "Yes. AutoCedar is configured to use the local Codex CLI "
                    "login for internal authoring calls. Deterministic code "
                    "still handles confirmations, verification, synthesis, and "
                    "HITL review gates."
                )
            return (
                "Yes. AutoCedar uses an Anthropic chat model for open-ended "
                "conversation when ANTHROPIC_API_KEY is loaded. Deterministic "
                "code still handles confirmations, draft capture, verification, "
                "synthesis, and HITL review gates."
            )
        if _mentions(lowered, "api key", "chat model", "model working"):
            return (
                "I do not currently see ANTHROPIC_API_KEY in the process "
                "environment. AutoCedar loads the nearest .env at startup; if "
                "that file contains the key, restart the TUI from that project "
                "directory."
            )
        if lowered in {"you didn't answer my question", "you didnt answer my question"}:
            return "You are right. That was a fallback response, not a real answer."
        return fallback

    def _call_chat_model(self, raw: str) -> str:
        import anthropic

        system, messages = self._chat_request(raw)
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=self.llm_model,
            max_tokens=800,
            thinking={"type": "adaptive"},
            output_config={"effort": self.llm_effort},
            system=system,
            messages=messages,
        )
        for block in response.content:
            if getattr(block, "type", None) == "text":
                return block.text
        return ""

    def _stream_chat_model(self, raw: str) -> str:
        system, messages = self._chat_request(raw)
        client = self._make_anthropic_client()
        chunks: list[str] = []
        self.call_from_thread(self._start_stream_output)
        with client.messages.stream(
            model=self.llm_model,
            max_tokens=800,
            thinking={"type": "adaptive"},
            output_config={"effort": self.llm_effort},
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                if not text:
                    continue
                chunks.append(text)
                self.call_from_thread(self._update_stream_output, "".join(chunks))
        answer = "".join(chunks)
        self.call_from_thread(self._finish_stream_output, answer)
        return answer

    def _make_anthropic_client(self) -> Any:
        import anthropic

        return anthropic.Anthropic()

    def _chat_request(self, raw: str) -> tuple[str, list[dict[str, str]]]:
        draft = "\n".join(self.draft_lines[-12:]) or "(empty)"
        state = self._state_snapshot(for_model=True)
        process_context = self._process_context()
        tui_legend = self._tui_legend_context()
        history = "\n".join(
            f"User: {user}\nAutoCedar: {assistant}"
            for user, assistant in self.chat_history[-4:]
        ) or "(none)"
        system = (
            "You are AutoCedar, a concise conversational interface for a "
            "human-in-the-loop Cedar policy authoring tool. Talk like a useful "
            "engineering product, not a command manual. You can help the user "
            "draft policy requirements, author a Cedar policy with HITL atom "
            "review, verify a workspace, synthesize benchmark scenarios, save "
            "or show a draft, and explain whether a spec or schema is needed. "
            "You have current TUI state, process context, and TUI legend "
            "context in the user message. Use that context when answering "
            "questions about the backend process, schema behavior, what is "
            "pending, whether drafting is active, or what UI labels mean. "
            "Do not invent capabilities beyond the process context. "
            "Do not claim to execute actions in chat; execution is handled by "
            "the app after confirmation. Keep answers to one or two short "
            "paragraphs unless the user asks for detail."
        )
        user_turn = (
            f"Current TUI state:\n{state}\n\n"
            f"AutoCedar process context:\n{process_context}\n\n"
            f"TUI legend context:\n{tui_legend}\n\n"
            f"Recent conversation:\n{history}\n\n"
            f"Current working draft:\n{draft}\n\n"
            f"User just said: {raw}"
        )
        return system, [{"role": "user", "content": user_turn}]

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
                return propose_schema_atoms(text, llm)

            def property_proposer(text: str, schema_path: str) -> list[Any]:
                return propose_property_atoms(text, schema_path, llm)

            def property_repairer(
                text: str,
                schema_path: str,
                rejected_atom: Any,
                reason: str,
                prior_atoms: list[Any],
            ) -> Any:
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

            if not options.auto_approve:
                review_atom.begin_stage = reviewer.begin_stage  # type: ignore[attr-defined]
                review_atom.end_stage = reviewer.end_stage  # type: ignore[attr-defined]
                review_atom.schema_ready = reviewer.schema_ready  # type: ignore[attr-defined]
                review_atom.property_plan_ready = reviewer.property_plan_ready  # type: ignore[attr-defined]

            kwargs: dict[str, Any] = {}
            if options.schema is None:
                kwargs["propose_schema_atoms"] = schema_proposer

            result = author_pipeline(
                spec_path=options.spec,
                output_dir=options.out,
                session_id=options.session_id,
                review_atom=review_atom,
                propose_property_atoms=property_proposer,
                repair_property_atom=property_repairer,
                synthesize=make_harness_synthesizer(
                    phase1_model=options.model or self.llm_model,
                    phase2_model=options.model or self.llm_model,
                    no_review=True,
                    quiet=True,
                    output_callback=lambda text: self.call_from_thread(
                        self._write,
                        text,
                    ),
                ),
                schema_path_override=str(options.schema) if options.schema else None,
                **kwargs,
            )
            self.call_from_thread(
                self._register_authoring_artifacts,
                result.session_dir,
                result.candidate_path,
                schema_override=options.schema,
            )
            lines = [
                f"[bold {GREEN}]Authoring complete.[/]",
                f"session:   {result.session_dir}",
                f"approved:  {result.final_user_approved}",
            ]
            if result.candidate_path:
                lines.append(f"candidate: {result.candidate_path}")
            if result.notes:
                lines.append("notes:")
                lines.extend(f"  - {note}" for note in result.notes)
            self.call_from_thread(self._write, "\n".join(lines))
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
        if self.pending_review is None:
            self.active_task = "idle"
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

    def _start_stream_output(self) -> None:
        stream = self.query_one("#stream", Static)
        stream.display = True
        stream.update(self._assistant_line(f"[dim {MUTED}]thinking...[/]"))

    def _update_stream_output(self, text: str) -> None:
        stream = self.query_one("#stream", Static)
        stream.display = True
        stream.update(
            self._assistant_line(
                f"{escape(text)}[dim {MUTED}]▌[/]",
            ),
        )

    def _finish_stream_output(self, text: str) -> None:
        self._clear_stream_output()
        if text:
            self._say(escape(text))

    def _clear_stream_output(self) -> None:
        stream = self.query_one("#stream", Static)
        stream.update("")
        stream.display = False

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
        key_state = "set" if is_real_anthropic_api_key(os.environ.get(ANTHROPIC_API_KEY)) else "not set"
        busy_color = AMBER if self.busy else TEAL
        drafting_color = GREEN if self.drafting_active else MUTED
        review_color = CORAL if self.pending_review is not None else MUTED
        action_color = AMBER if self.pending_action is not None else MUTED
        key_color = TEAL if key_state == "set" else CORAL
        text = (
            f"[bold {COPPER}]Session[/]\n\n"
            f"[dim {MUTED}]current task[/]\n[bold {CREAM}]{escape(self.active_task)}[/]\n\n"
            f"[dim {MUTED}]agent state[/]\n[bold {busy_color}]{'working' if self.busy else 'ready'}[/]\n\n"
            f"[dim {MUTED}]model[/]\n[bold {CREAM}]{escape(_short_model(self.llm_model))}[/]\n\n"
            f"[dim {MUTED}]effort[/]\n[bold {CREAM}]{escape(self.llm_effort)}[/]\n\n"
            f"[dim {MUTED}]api key[/]\n[bold {key_color}]{key_state}[/]\n\n"
            f"[dim {MUTED}]pending atom review[/]\n[bold {review_color}]{review_state}[/]\n\n"
            f"[dim {MUTED}]pending yes/no[/]\n[bold {action_color}]{action_state}[/]\n\n"
            f"[dim {MUTED}]draft capture[/]\n[bold {drafting_color}]{drafting_state}[/]\n\n"
            f"[dim {MUTED}]draft lines[/]\n[bold {CREAM}]{draft_state}[/]\n\n"
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
            f"api key: {'set' if is_real_anthropic_api_key(os.environ.get(ANTHROPIC_API_KEY)) else 'not set'}",
            f"latest session: {self.latest_session_dir or 'none'}",
            f"latest schema: {self.latest_schema_path or 'none'}",
            f"latest policy: {self.latest_policy_path or 'none'}",
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
                "Deterministic routing handles concrete actions: draft capture gates, author, verify, synthesize, save, show, artifact inspection, clipboard copy, clear, quit, and slash shortcuts.",
                "Open-ended questions should be answered conversationally from this context, not by deterministic process-answer branches.",
                "Authoring from prose without a schema override: AutoCedar saves the prose spec, runs Stage 1 schema atomization, proposes entity/action/attribute/type-alias atoms, and sends each proposed schema atom through HITL review before composing the schema.",
                "Authoring with a schema path: AutoCedar uses that existing schema directly and skips Stage 1 schema atomization/review.",
                "Stage 2 property atoms: AutoCedar proposes property atoms from the spec and validated schema, symbolically verifies each atom, and sends each proposed property through the same HITL review callback before compiling the verification plan.",
                "The authoring engine receives clean inputs: saved spec text, optional schema path, and HITL review decisions. The chat transcript is not passed into authoring.",
                "Runtime LLM settings are user-selectable inside the TUI through /settings, /model, /effort, and /apikey. The selected model is used for chat, authoring atomization, and default synthesis phase models unless an explicit command overrides it. Effort is used for chat and authoring atomization calls that support adaptive thinking.",
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


def interpret_natural_language(raw: str, *, has_draft: bool) -> NaturalLanguageIntent:
    """Map input into action intents while leaving open-ended text for chat."""
    text = raw.strip()
    lowered = _squash(text).lower()
    if not lowered:
        return NaturalLanguageIntent("message", message="I’m here.")

    if _looks_like_greeting(lowered):
        return NaturalLanguageIntent(
            "message",
            message=(
                "Hey. Ask me questions normally, or say “start a policy draft” "
                "when you want me to begin capturing requirements."
            ),
        )
    if _looks_like_frustration(lowered):
        return NaturalLanguageIntent(
            "message",
            message=(
                "Fair. I should only begin policy drafting after an explicit "
                "approval. Until then, I’ll treat normal language as conversation."
            ),
        )
    if _looks_like_meta_complaint(lowered):
        return NaturalLanguageIntent(
            "message",
            message=(
                "That sounds like feedback about the session, not policy text. "
                "I won’t add it to the draft."
            ),
        )
    if _looks_like_help(lowered):
        return NaturalLanguageIntent("help")
    if lowered in {"quit", "exit", "bye", "goodbye"}:
        return NaturalLanguageIntent("quit")
    settings_update = _settings_update_from_nl(text)
    if settings_update is not None:
        return NaturalLanguageIntent("settings", settings_update=settings_update)
    if _mentions(lowered, "clear transcript", "clear screen", "clear chat"):
        return NaturalLanguageIntent("clear_transcript")
    if _mentions(lowered, "clear draft", "clear spec", "start over", "reset draft") or (
        has_draft and lowered in {"clear it", "wipe it", "reset it", "delete it"}
    ):
        return NaturalLanguageIntent("clear_draft")
    if _is_start_draft_request(lowered):
        return NaturalLanguageIntent("start_draft")
    if _is_show_draft_request(lowered):
        return NaturalLanguageIntent("show_draft")
    if _is_save_request(lowered):
        return NaturalLanguageIntent("save_draft", path=_extract_save_path(text))
    if _is_verify_request(lowered):
        return NaturalLanguageIntent(
            "verify",
            workspace=_extract_workspace_path(text) or Path("workspace"),
        )
    if _is_synthesize_request(lowered):
        options = _synthesize_options_from_nl(text)
        if options is None:
            return NaturalLanguageIntent(
                "message",
                message="Tell me which scenario to synthesize.",
            )
        return NaturalLanguageIntent("synthesize", synthesize_options=options)
    if _is_author_request(lowered):
        options, from_draft = _author_options_from_nl(text, has_draft=has_draft)
        if options is None:
            return NaturalLanguageIntent(
                "message",
                message=(
                    "I need either a spec path or a draft. Say “start a policy "
                    "draft” first, then give me requirements and say “author this”."
                ),
            )
        return NaturalLanguageIntent(
            "author",
            author_options=options,
            from_draft=from_draft,
        )
    if _looks_like_question(lowered):
        return NaturalLanguageIntent(
            "message",
            message=(
                "I can help draft a Cedar policy spec, author it through HITL "
                "review, verify a workspace, or synthesize a benchmark scenario. "
                "Say “start a policy draft” when you want me to begin capturing "
                "requirements, or say something like “verify the workspace”."
            ),
        )
    if not _looks_like_policy_requirement(lowered):
        return NaturalLanguageIntent(
            "message",
            message=(
                "I’m listening. I’ll treat this as conversation unless you ask "
                "me to start drafting or approve a draft-capture prompt."
            ),
        )

    return NaturalLanguageIntent("append_draft")


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _mentions(text: str, *phrases: str) -> bool:
    return any(phrase in text for phrase in phrases)


def _settings_update_from_nl(raw: str) -> SettingsUpdate | None:
    text = _squash(raw)
    lowered = text.lower()

    if lowered in {
        "settings",
        "show settings",
        "show me settings",
        "show runtime settings",
        "show model settings",
        "what model are you using",
        "what model are you using?",
        "what effort are you using",
        "what effort are you using?",
    }:
        return SettingsUpdate(show=True)

    if _mentions(lowered, "api key", "apikey", "anthropic key", "anthropic api key"):
        if _mentions(lowered, "clear api key", "unset api key", "remove api key", "delete api key"):
            return SettingsUpdate(clear_api_key=True)
        key = _extract_api_key(text)
        if key:
            return SettingsUpdate(api_key=key)
        if lowered.startswith((
            "set api key",
            "set the api key",
            "add api key",
            "add the api key",
            "update api key",
            "use api key",
            "set anthropic api key",
            "set the anthropic api key",
        )):
            return SettingsUpdate(prompt_api_key=True)

    model = _extract_settings_model(text)
    effort = _extract_effort(text)
    if model or effort:
        return SettingsUpdate(model=model, effort=effort)

    return None


def _extract_settings_model(raw: str) -> str | None:
    match = re.search(
        r"\b(?:set|switch|change|use)\s+(?:the\s+)?(?:llm\s+|chat\s+|authoring\s+)?"
        r"model(?:\s+(?:to|as))?\s+(?P<value>[^\s]+)",
        raw,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return _clean_path_token(match.group("value"))


def _extract_effort(raw: str) -> str | None:
    match = re.search(
        r"\b(?:set|switch|change|use)\s+(?:the\s+)?effort(?:\s+(?:to|as))?\s+"
        r"(?P<value>low|medium|high|max)\b",
        raw,
        flags=re.IGNORECASE,
    )
    if not match:
        match = re.search(
            r"\beffort\s+(?P<value>low|medium|high|max)\b",
            raw,
            flags=re.IGNORECASE,
        )
    return _normalize_effort(match.group("value")) if match else None


def _extract_api_key(raw: str) -> str | None:
    match = re.search(
        r"\bANTHROPIC_API_KEY\s*=\s*(?P<value>[^\s]+)",
        raw,
        flags=re.IGNORECASE,
    )
    if match:
        return _strip_wrapping_quotes(match.group("value"))
    match = re.search(r"\b(?P<value>sk-ant-[A-Za-z0-9_\-.]+)", raw)
    if match:
        return _strip_wrapping_quotes(match.group("value"))
    match = re.search(
        r"\b(?:api[- ]?key|apikey|anthropic(?:\s+api)?\s+key)"
        r"(?:\s+(?:to|as|is))?\s+(?P<value>[^\s]+)",
        raw,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    value = _strip_wrapping_quotes(match.group("value"))
    if value.lower() in {"clear", "unset", "remove", "delete", "cancel"}:
        return None
    return value


def _looks_like_help(text: str) -> bool:
    return text in {"help", "commands", "shortcuts"} or _mentions(
        text,
        "show me commands",
        "show shortcuts",
    )


def _looks_like_greeting(text: str) -> bool:
    return text in {
        "hey",
        "hi",
        "hello",
        "yo",
        "sup",
        "good morning",
        "good afternoon",
        "good evening",
    }


def _looks_like_frustration(text: str) -> bool:
    return text in {
        "really",
        "really?",
        "seriously",
        "seriously?",
        "bruh",
        "my guy",
        "come on",
        "what's wrong with you",
        "whats wrong with you",
    }


def _looks_like_meta_complaint(text: str) -> bool:
    return text.startswith((
        "i said ",
        "i told ",
        "you said ",
        "u said ",
        "you didn't ",
        "you didnt ",
        "it won't ",
        "it wont ",
        "this won't ",
        "this wont ",
    ))


def _looks_like_question(text: str) -> bool:
    return text.endswith("?") or text.startswith((
        "are ",
        "can you ",
        "could you ",
        "do ",
        "does ",
        "how ",
        "is ",
        "tell me ",
        "what ",
        "why ",
    ))


def _looks_like_policy_requirement(text: str) -> bool:
    if len(text.split()) < 4:
        return False
    if _looks_like_domain_setup_statement(text):
        return True
    if _mentions(
        text,
        " can ",
        " cannot ",
        " can't ",
        " may ",
        " must ",
        " should ",
        " should not ",
        " only ",
        " deny ",
        " allow ",
        " permit ",
        " forbid ",
        " access ",
        " read ",
        " write ",
        " edit ",
        " delete ",
        " approve ",
        " view ",
        " create ",
        " update ",
        " owner ",
        " admin ",
        " admins ",
        " user ",
        " users ",
        " role ",
        " roles ",
        " resource ",
        " resources ",
        " document ",
        " documents ",
        " entity ",
        " entities ",
        " action ",
        " actions ",
        " policy ",
    ):
        return True
    return text.startswith((
        "only ",
        "allow ",
        "deny ",
        "permit ",
        "forbid ",
        "users ",
        "admins ",
        "owners ",
    ))


def _looks_like_active_draft_statement(raw: str) -> bool:
    text = _squash(raw).lower()
    if not text or _looks_like_question(text) or _looks_like_greeting(text):
        return False
    if _looks_like_frustration(text) or _looks_like_meta_complaint(text):
        return False
    return _looks_like_policy_requirement(text) or _looks_like_domain_setup_statement(text)


def _is_show_draft_request(text: str) -> bool:
    return (
        text in {
            "show draft",
            "show the draft",
            "show me the draft",
            "display draft",
            "display the draft",
            "view draft",
            "view the draft",
            "draft state",
            "show draft state",
            "show the draft state",
            "current draft",
            "current spec",
            "what is in the draft",
            "what's in the draft",
            "whats in the draft",
            "what is in my draft",
            "what's in my draft",
            "whats in my draft",
        }
        or text.startswith((
            "show the current draft",
            "show current draft",
            "show me current draft",
            "show me the current draft",
            "peek at the draft",
            "list the draft",
        ))
    )


def _looks_like_domain_setup_statement(text: str) -> bool:
    return (
        _mentions(
            text,
            " system has ",
            " system contains ",
            " has users ",
            " has documents ",
            " has resources ",
            " has entities ",
            " includes users ",
            " includes documents ",
            " includes resources ",
            " includes entities ",
            " there are users ",
            " there are documents ",
            " there are resources ",
            " there are entities ",
        )
        or re.search(r"\b(users?|documents?|resources?|entities|actions?)\b.*\b(users?|documents?|resources?|entities|actions?)\b", text)
        is not None
    )


def _is_save_request(text: str) -> bool:
    return text.startswith(("save ", "write ")) or text in {
        "save this",
        "save draft",
        "save the draft",
    }


def _is_start_draft_request(text: str) -> bool:
    return (
        text in {
            "start a policy draft",
            "start policy draft",
            "start drafting",
            "begin drafting",
            "begin a policy draft",
            "new policy draft",
            "draft a policy",
        }
        or text.startswith((
            "start a draft",
            "start the draft",
            "start drafting ",
            "begin drafting ",
            "begin a draft",
            "begin the draft",
            "let's draft",
            "lets draft",
        ))
    )


def _is_verify_request(text: str) -> bool:
    return text.startswith(("verify", "check the workspace", "check workspace")) or (
        "run verification" in text
    )


def _is_author_request(text: str) -> bool:
    return text.startswith((
        "author",
        "build policy",
        "generate policy",
        "make policy",
        "create policy",
    ))


def _is_synthesize_request(text: str) -> bool:
    return text.startswith(("synthesize", "run synthesis", "run scenario"))


def _extract_save_path(raw: str) -> Path | None:
    match = re.search(
        r"\b(?:save|write)(?:\s+(?:this|it|draft|the draft|spec|policy))*"
        r"\s+(?:as|to)\s+(?P<path>[^\s]+)",
        raw,
        flags=re.IGNORECASE,
    )
    if match:
        return Path(_clean_path_token(match.group("path")))
    for token in _path_tokens(raw):
        if token.suffix in {".md", ".txt"}:
            return token
    return None


def _extract_workspace_path(raw: str) -> Path | None:
    lowered = raw.lower()
    match = re.search(r"\b(?:workspace|directory|dir)\s+(?P<path>[^\s]+)", raw)
    if match and match.group("path").lower() not in {"and", "please", "now"}:
        return Path(_clean_path_token(match.group("path")))
    for token in _path_tokens(raw):
        if str(token) == "workspace" or "workspace" in str(token):
            return token
    if "workspace" in lowered:
        return Path("workspace")
    paths = _path_tokens(raw)
    return paths[0] if paths else None


def _author_options_from_nl(
    raw: str,
    *,
    has_draft: bool,
) -> tuple[AuthorOptions | None, bool]:
    schema = _extract_schema_path(raw)
    spec = _extract_spec_path(raw)
    lowered = raw.lower()
    from_draft = False
    if spec is None and (
        has_draft
        and _mentions(lowered, "this", "draft", "it", "current spec", "current draft")
    ):
        spec = DRAFT_PATH
        from_draft = True
    if spec is None:
        return None, False
    return (
        AuthorOptions(
            spec=spec,
            out=_extract_output_path(raw) or Path("autocedar-runs"),
            session_id=_extract_session_id(raw),
            schema=schema,
            model=_extract_author_model(raw),
            effort=_extract_effort(raw),
            auto_approve=_mentions(lowered, "auto approve", "auto-approve", "without review"),
        ),
        from_draft,
    )


def _synthesize_options_from_nl(raw: str) -> SynthesizeOptions | None:
    out = _extract_output_path(raw) or Path("eval_runs")
    paths = [path for path in _path_tokens(raw) if path != out]
    scenarios = [_resolve_scenario_path(path) for path in paths]
    scenarios = [path for path in scenarios if path is not None]
    if not scenarios:
        return None
    max_iters_match = re.search(
        r"\b(?:max(?:imum)?(?:\s+(?:iters|iterations))?|iters?)\D+(?P<n>\d+)",
        raw,
        flags=re.IGNORECASE,
    )
    return SynthesizeOptions(
        scenarios=scenarios,
        out=out,
        run_id=_extract_run_id(raw),
        phase1_model=_extract_phase_model(raw, "phase1"),
        phase2_model=_extract_phase_model(raw, "phase2"),
        max_iters=int(max_iters_match.group("n")) if max_iters_match else None,
        gen_references=_mentions(
            raw.lower(),
            "generate references",
            "gen references",
            "regenerate references",
            "with references",
        ),
        no_review=_mentions(raw.lower(), "no review", "without review", "skip review"),
    )


def _extract_output_path(raw: str) -> Path | None:
    match = re.search(
        r"\b(?:out|output|output dir|output directory|into|under)\s+(?P<path>[^\s]+)",
        raw,
        flags=re.IGNORECASE,
    )
    if match:
        return Path(_clean_path_token(match.group("path")))
    return None


def _extract_run_id(raw: str) -> str | None:
    match = re.search(r"\brun[-\s]?id\s+(?P<value>[^\s]+)", raw, flags=re.IGNORECASE)
    return _clean_path_token(match.group("value")) if match else None


def _extract_session_id(raw: str) -> str | None:
    match = re.search(
        r"\bsession[-\s]?id\s+(?P<value>[^\s]+)",
        raw,
        flags=re.IGNORECASE,
    )
    return _clean_path_token(match.group("value")) if match else None


def _extract_author_model(raw: str) -> str | None:
    match = re.search(
        r"(?<!phase1\s)(?<!phase2\s)\bmodel\s+(?P<value>[^\s]+)",
        raw,
        flags=re.IGNORECASE,
    )
    return _clean_path_token(match.group("value")) if match else None


def _extract_phase_model(raw: str, phase: str) -> str | None:
    spaced = phase.replace("phase", "phase ")
    match = re.search(
        rf"\b(?:{phase}|{spaced})[-\s]?model\s+(?P<value>[^\s]+)",
        raw,
        flags=re.IGNORECASE,
    )
    return _clean_path_token(match.group("value")) if match else None


def _extract_schema_path(raw: str) -> Path | None:
    match = re.search(r"\bschema\s+(?P<path>[^\s]+)", raw, flags=re.IGNORECASE)
    if match:
        return Path(_clean_path_token(match.group("path")))
    for token in _path_tokens(raw):
        if token.suffix == ".cedarschema":
            return token
    return None


def _extract_spec_path(raw: str) -> Path | None:
    schema = _extract_schema_path(raw)
    for token in _path_tokens(raw):
        if token == schema:
            continue
        if token.suffix in {".md", ".txt"}:
            return token
    return None


def _path_tokens(raw: str) -> list[Path]:
    try:
        tokens = shlex.split(raw)
    except ValueError:
        tokens = raw.split()
    paths: list[Path] = []
    for token in tokens:
        cleaned = _clean_path_token(token)
        lowered = cleaned.lower()
        if not cleaned or lowered in _COMMON_WORDS:
            continue
        path = Path(cleaned)
        if _looks_like_path(cleaned, path):
            paths.append(path)
    return paths


def _clean_path_token(token: str) -> str:
    return token.strip().strip("\"'`").rstrip(".,;:)")


def _looks_like_path(token: str, path: Path) -> bool:
    return (
        "/" in token
        or token.startswith(".")
        or token == "workspace"
        or token.startswith("cedarbench")
        or path.suffix in {".md", ".txt", ".cedarschema"}
        or path.exists()
        or (Path("cedarbench/scenarios/realworld") / token).exists()
        or (Path("cedarbench/scenarios") / token).exists()
    )


def _resolve_scenario_path(path: Path) -> Path | None:
    if path.exists() or "/" in str(path):
        return path
    realworld = Path("cedarbench/scenarios/realworld") / str(path)
    if realworld.exists():
        return realworld
    scenario = Path("cedarbench/scenarios") / str(path)
    if scenario.exists():
        return scenario
    return path


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
        "properties: propose and symbolically verify Stage 2 property atoms, then pause for HITL review.",
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


def _short_model(model: str) -> str:
    if len(model) <= 30:
        return model
    return model[:27] + "..."


def run_tui() -> int:
    load_dotenv()
    AutoCedarApp().run()
    return 0


def _chat_failure_message(exc: Exception) -> str:
    return (
        "The chat model call failed, so I’m not going to pretend that was "
        f"model-backed. Error: {exc.__class__.__name__}: {escape(str(exc))}"
    )
