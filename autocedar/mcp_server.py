"""Stdio MCP server that lets coding agents drive AutoCedar.

Agents such as Claude Code and Codex connect to ``autocedar mcp`` and call the
tools below. The authoring pipeline runs in a background thread, as it does in
the TUI, and pauses at every atom until a decision arrives through
``author_review``. That decision must be the human user's: the agent shows the
atom to the user and relays their answer. It never approves atoms on its own,
because AutoCedar's correctness claim rests on human-approved targets.

The protocol layer is a small JSON-RPC 2.0 loop over newline-delimited stdio
messages, which keeps the package free of extra dependencies.
"""

from __future__ import annotations

import datetime
import json
import sys
import threading
import traceback
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, TextIO

from autocedar import __version__
from autocedar.atoms import PropertyAtom
from autocedar.corpus import AtomDecision
from autocedar.intent_map import IntentMap, PermissionsQuestion, SliceQuestion
from autocedar.ui.terminal import (
    ReviewedAtom,
    _apply_field_edit,
    _approval_needs_failed_property_confirmation,
    _render_review_atom,
    render_property_reference,
    render_schema_declaration,
)

SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
DEFAULT_WAIT_SECONDS = 20.0
MAX_WAIT_SECONDS = 50.0
MAX_EVENTS = 200

SERVER_INSTRUCTIONS = (
    "AutoCedar turns natural-language access-control requirements into Cedar "
    "policies that are checked against a reviewed target. Start with "
    "`doctor` to confirm Cedar, SymCC and the model provider are set up. "
    "`author_start` runs the authoring pipeline; whenever a status contains "
    "`pending_review`, show the atom to the user exactly as given and ask "
    "them to approve, reject (with a reason) or edit it. The first item is the "
    "intent map, which can be approved or rejected with a reason. If the "
    "requirements do not say whether they list every permission, a yes/no "
    "question follows: approve means yes, reject means no. Submit only the "
    "user's own decision with `author_review`; never decide for them. "
    "`verify` checks an existing workspace's candidate.cedar against its "
    "verification_plan.py."
)


# ---------------------------------------------------------------------------
# Authoring runs.
# ---------------------------------------------------------------------------


class PausedByUser(RuntimeError):
    """Raised inside the pipeline thread when the user pauses a run."""


@dataclass
class _ReviewRequest:
    request_id: int
    atom: Any
    stage: str
    index: int
    total: Optional[int]
    event: threading.Event = field(default_factory=threading.Event)
    result: Optional[ReviewedAtom] = None
    paused: bool = False
    edit_log: dict[str, Any] = field(default_factory=dict)
    failed_checks_confirmed: bool = False


class _McpReviewer:
    """Atom reviewer that hands each atom to the MCP client and blocks."""

    def __init__(self, run: "AuthoringRun") -> None:
        self.run = run
        self.sequence = 0
        self.stage_label = "Atom review"
        self.stage_total: Optional[int] = None
        self.stage_index = 0

    def begin_stage(self, label: str, total: Optional[int]) -> None:
        self.stage_label = label
        self.stage_total = total
        self.stage_index = 0
        self.run.add_event({"event": "stage_started", "stage": label, "total": total})

    def end_stage(self, label: str, approved: int, rejected: int) -> None:
        self.run.add_event({
            "event": "stage_finished",
            "stage": label,
            "approved": approved,
            "rejected": rejected,
        })

    def schema_ready(self, schema_text: str) -> None:
        self.run.add_event({"event": "schema_ready", "schema": schema_text})

    def property_plan_ready(self, properties: list[Any]) -> None:
        self.run.add_event({"event": "property_plan_ready", "properties": len(properties)})

    def property_progress(self, payload: dict[str, Any]) -> None:
        self.run.add_event({"event": "property_progress", **_jsonable(payload)})

    def __call__(self, atom: Any) -> ReviewedAtom:
        self.sequence += 1
        self.stage_index += 1
        total = self.stage_total
        if total is not None and self.stage_index > total:
            total = None
        request = _ReviewRequest(
            request_id=self.sequence,
            atom=atom,
            stage=self.stage_label,
            index=self.stage_index,
            total=total,
        )
        self.run.set_pending(request)
        request.event.wait()
        if request.paused or request.result is None:
            raise PausedByUser(
                "Authoring paused before this atom was decided. Resume the "
                "session with `author_start` and `resume_session`."
            )
        return request.result


class AuthoringRun:
    """One authoring session running in a background thread."""

    def __init__(
        self,
        run_id: str,
        target: Callable[["_McpReviewer"], Any],
        session_dir: Optional[Path] = None,
    ) -> None:
        self.run_id = run_id
        self.session_dir = session_dir
        self._target = target
        self._cond = threading.Condition()
        self.state = "running"
        self.pending: Optional[_ReviewRequest] = None
        self.events: list[dict[str, Any]] = []
        self.result: Any = None
        self.error: str = ""
        self.reviewer = _McpReviewer(self)
        self.thread = threading.Thread(target=self._run, name=f"autocedar-{run_id}", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def _run(self) -> None:
        try:
            result = self._target(self.reviewer)
        except PausedByUser as exc:
            self._finish("paused", error=str(exc))
        except Exception as exc:  # noqa: BLE001 - reported to the client
            detail = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            self._finish("error", error=detail)
        else:
            self._finish("finished", result=result)

    def _finish(self, state: str, *, result: Any = None, error: str = "") -> None:
        with self._cond:
            self.state = state
            self.result = result
            self.error = error
            self.pending = None
            self._cond.notify_all()

    def add_event(self, event: dict[str, Any]) -> None:
        with self._cond:
            self.events.append(event)
            del self.events[:-MAX_EVENTS]
            self._cond.notify_all()

    def set_pending(self, request: _ReviewRequest) -> None:
        with self._cond:
            self.pending = request
            self.state = "awaiting_review"
            self._cond.notify_all()

    def wait(self, seconds: float) -> None:
        """Block until a review is pending, the run ends, or time runs out."""
        with self._cond:
            self._cond.wait_for(lambda: self.state != "running", timeout=seconds)

    def resolve(self, request: _ReviewRequest, result: ReviewedAtom) -> None:
        with self._cond:
            request.result = result
            self.pending = None
            self.state = "running"
            request.event.set()

    def pause(self) -> None:
        with self._cond:
            request = self.pending
            if request is None:
                return
            request.paused = True
            self.pending = None
            request.event.set()



def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _render_pending(request: _ReviewRequest) -> dict[str, Any]:
    atom = request.atom
    is_property = isinstance(atom, PropertyAtom)
    rendered = _render_review_atom(atom, request.index, request.total or request.index)
    options = [
        "approve",
        "reject (give a reason)",
        "edit (field=value lines, then review again)",
    ]
    if isinstance(atom, IntentMap):
        kind, cedar = "intent_map", json.dumps(atom.to_dict(), indent=2)
        options = options[:2]
    elif isinstance(atom, SliceQuestion):
        kind, cedar = "slice_question", json.dumps(atom.to_dict(), indent=2)
        options = [
            "approve (yes: the document grants this scope without conditions)",
            "reject (no: remove this way to allow it)",
        ]
    elif isinstance(atom, PermissionsQuestion):
        kind, cedar = "permissions_question", json.dumps(atom.to_dict(), indent=2)
        options = [
            "approve (yes: the list of permissions is complete)",
            "reject (no: the listed permissions are examples)",
        ]
    else:
        kind = "property" if is_property else "schema"
        cedar = render_property_reference(atom) if is_property else render_schema_declaration(atom)
    pending: dict[str, Any] = {
        "request_id": request.request_id,
        "stage": request.stage,
        "index": request.index,
        "total": request.total,
        "kind": kind,
        "name": getattr(atom, "name", ""),
        "summary": getattr(atom, "plain_english_summary", ""),
        "source_excerpt": getattr(atom, "source_excerpt", ""),
        "cedar": cedar,
        "rendered": rendered,
        "options": options,
    }
    if is_property:
        pending["constraint_type"] = atom.constraint_type
        pending["action"] = atom.action
        pending["symbolic_verified"] = bool(atom.symbolic_verified)
        pending["symbolic_checks"] = list(atom.symbolic_verification_log)
    return pending


def _summarize_result(result: Any) -> dict[str, Any]:
    candidate_path = getattr(result, "candidate_path", None)
    candidate = Path(candidate_path) if candidate_path else None
    completed = bool(candidate and str(candidate) not in {"", "."} and candidate.is_file())
    summary: dict[str, Any] = {
        "session_dir": str(getattr(result, "session_dir", "")),
        "completed": completed,
        "final_user_approved": bool(getattr(result, "final_user_approved", False)),
        "notes": list(getattr(result, "notes", []) or []),
    }
    plan = getattr(result, "plan", None)
    if plan is not None:
        summary["approved_properties"] = [
            {"name": atom.name, "kind": atom.constraint_type, "action": atom.action}
            for atom in getattr(plan, "properties", [])
        ]
    if completed and candidate is not None:
        summary["candidate_path"] = str(candidate)
        summary["candidate_cedar"] = candidate.read_text()
    return summary


# ---------------------------------------------------------------------------
# Tools.
# ---------------------------------------------------------------------------


class ToolError(Exception):
    """A tool call failed in a way the agent should see and fix."""


@dataclass
class _Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any]], dict[str, Any]]


def _wait_arg(arguments: dict[str, Any]) -> float:
    try:
        wait = float(arguments.get("wait_seconds", DEFAULT_WAIT_SECONDS))
    except (TypeError, ValueError) as exc:
        raise ToolError("wait_seconds must be a number") from exc
    return max(0.0, min(wait, MAX_WAIT_SECONDS))


def _path_arg(arguments: dict[str, Any], key: str, *, must_exist: bool) -> Path:
    raw = arguments.get(key)
    if not isinstance(raw, str) or not raw.strip():
        raise ToolError(f"`{key}` is required")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if must_exist and not path.exists():
        raise ToolError(f"`{key}` does not exist: {path}")
    return path


class AutoCedarTools:
    """Tool implementations, kept separate from the protocol loop for testing."""

    def __init__(
        self,
        *,
        pipeline_factory: Optional[Callable[..., Callable[[_McpReviewer], Any]]] = None,
    ) -> None:
        self.runs: dict[str, AuthoringRun] = {}
        self._pipeline_factory = pipeline_factory or _default_pipeline_factory
        self.tools = [
            _Tool(
                "doctor",
                "Check that the model provider, Cedar CLI, SymCC and CVC5 are set up. "
                "Run this first; each failed check comes with the command that fixes it.",
                {
                    "type": "object",
                    "properties": {
                        "live_symcc": {
                            "type": "boolean",
                            "description": "Also run a live SymCC smoke test (default true).",
                        },
                    },
                    "additionalProperties": False,
                },
                self.doctor,
            ),
            _Tool(
                "verify",
                "Verify a workspace's candidate.cedar against its schema.cedarschema and "
                "verification_plan.py with cedar validate and cedar symcc. Returns every "
                "check with its counterexample when it fails.",
                {
                    "type": "object",
                    "properties": {
                        "workspace": {
                            "type": "string",
                            "description": "Absolute path to the workspace directory.",
                        },
                    },
                    "required": ["workspace"],
                    "additionalProperties": False,
                },
                self.verify,
            ),
            _Tool(
                "author_start",
                "Start AutoCedar's human-in-the-loop authoring pipeline on a requirements "
                "document, or resume an earlier session. Returns a run_id and the run's "
                "status. When the status has `pending_review`, show that atom to the user and "
                "relay their decision with author_review.",
                {
                    "type": "object",
                    "properties": {
                        "spec_path": {
                            "type": "string",
                            "description": "Absolute path to the natural-language requirements file.",
                        },
                        "out_dir": {
                            "type": "string",
                            "description": "Absolute path of the directory for session output.",
                        },
                        "resume_session": {
                            "type": "string",
                            "description": "Absolute path of an earlier session directory to resume.",
                        },
                        "schema_path": {
                            "type": "string",
                            "description": "Optional existing Cedar schema; skips schema atom proposal.",
                        },
                        "session_id": {"type": "string"},
                        "provider": {
                            "type": "string",
                            "enum": ["codex", "claude-cli", "anthropic", "openai", "local"],
                            "description": "Model provider for this run (default: saved AutoCedar setting).",
                        },
                        "model": {"type": "string"},
                        "effort": {"type": "string", "enum": ["low", "medium", "high", "max"]},
                        "wait_seconds": {
                            "type": "number",
                            "description": f"How long to wait for the first review (max {MAX_WAIT_SECONDS:g}).",
                        },
                    },
                    "required": ["out_dir"],
                    "additionalProperties": False,
                },
                self.author_start,
            ),
            _Tool(
                "author_status",
                "Return an authoring run's status: running (with recent progress), "
                "awaiting_review (with the pending atom), paused, finished (with the "
                "verified Cedar policy), or error. Waits briefly for a change.",
                {
                    "type": "object",
                    "properties": {
                        "run_id": {"type": "string"},
                        "wait_seconds": {"type": "number"},
                    },
                    "required": ["run_id"],
                    "additionalProperties": False,
                },
                self.author_status,
            ),
            _Tool(
                "author_review",
                "Submit the USER's decision on the pending atom. Only call this with a "
                "decision the user gave you after seeing the atom; never approve, reject "
                "or edit on your own judgment. `edit` applies field=value edits and "
                "returns the edited atom for the user to review again.",
                {
                    "type": "object",
                    "properties": {
                        "run_id": {"type": "string"},
                        "request_id": {
                            "type": "integer",
                            "description": "The pending_review.request_id being answered.",
                        },
                        "decision": {"type": "string", "enum": ["approve", "reject", "edit"]},
                        "reason": {
                            "type": "string",
                            "description": "The user's reason (required for reject).",
                        },
                        "edits": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "field=value edits, e.g. plain_english_summary=...",
                        },
                        "confirm_failed_checks": {
                            "type": "boolean",
                            "description": (
                                "Set only when the user explicitly approves an atom whose "
                                "symbolic checks failed, after being told they failed."
                            ),
                        },
                        "wait_seconds": {"type": "number"},
                    },
                    "required": ["run_id", "request_id", "decision"],
                    "additionalProperties": False,
                },
                self.author_review,
            ),
            _Tool(
                "author_pause",
                "Pause an authoring run at its pending atom. Decisions so far are saved; "
                "continue later with author_start and resume_session.",
                {
                    "type": "object",
                    "properties": {"run_id": {"type": "string"}},
                    "required": ["run_id"],
                    "additionalProperties": False,
                },
                self.author_pause,
            ),
        ]
        self._by_name = {tool.name: tool for tool in self.tools}

    # -- dispatch -----------------------------------------------------------

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": t.name, "description": t.description, "inputSchema": t.input_schema}
            for t in self.tools
        ]

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        tool = self._by_name.get(name)
        if tool is None:
            raise ToolError(f"unknown tool: {name}")
        return tool.handler(arguments or {})

    # -- tools --------------------------------------------------------------

    def doctor(self, arguments: dict[str, Any]) -> dict[str, Any]:
        from autocedar.doctor import format_doctor_report, run_doctor

        report = run_doctor(live_symcc=bool(arguments.get("live_symcc", True)))
        return {
            "ok": not report.failed,
            "checks": [
                {"name": c.name, "status": c.status, "detail": c.detail, "fix": c.fix}
                for c in report.checks
            ],
            "report": format_doctor_report(report),
        }

    def verify(self, arguments: dict[str, Any]) -> dict[str, Any]:
        from autocedar.harness.orchestrator import run_verification

        workspace = _path_arg(arguments, "workspace", must_exist=True)
        if not (workspace / "candidate.cedar").exists():
            raise ToolError(f"candidate not found: {workspace / 'candidate.cedar'}")
        vr = run_verification(str(workspace))
        return {
            "passed": vr.loss == 0,
            "loss": vr.loss,
            "checks": [
                {
                    "name": r.check_name,
                    "type": r.check_type,
                    "description": r.description,
                    "passed": r.passed,
                    "counterexample": r.counterexample,
                    "tool_error": r.tool_error,
                }
                for r in vr.results
            ],
        }

    def author_start(self, arguments: dict[str, Any]) -> dict[str, Any]:
        out_dir = _path_arg(arguments, "out_dir", must_exist=False)
        resume = arguments.get("resume_session")
        if resume:
            resume_dir = _path_arg(arguments, "resume_session", must_exist=True)
            inputs = sorted((resume_dir / "input").glob("*"))
            if not inputs:
                raise ToolError(f"session has no input spec under {resume_dir / 'input'}")
            spec_path = inputs[0]
        else:
            resume_dir = None
            spec_path = _path_arg(arguments, "spec_path", must_exist=True)
        schema_path = (
            _path_arg(arguments, "schema_path", must_exist=True)
            if arguments.get("schema_path") else None
        )
        # Choose the session id here, in the pipeline's own format, so a paused
        # or failed run can still report the directory it resumes from.
        session_id = arguments.get("session_id") or (
            datetime.datetime.now(datetime.timezone.utc).strftime("session-%Y%m%d-%H%M%S-")
            + uuid.uuid4().hex[:8]
        )
        target = self._pipeline_factory(
            spec_path=spec_path,
            out_dir=out_dir,
            resume_from=resume_dir,
            schema_path=schema_path,
            session_id=session_id,
            provider=arguments.get("provider"),
            model=arguments.get("model"),
            effort=arguments.get("effort"),
        )
        run_id = uuid.uuid4().hex[:12]
        run = AuthoringRun(run_id, target, session_dir=out_dir / session_id)
        self.runs[run_id] = run
        run.start()
        run.wait(_wait_arg(arguments))
        return self._status(run)

    def author_status(self, arguments: dict[str, Any]) -> dict[str, Any]:
        run = self._run(arguments)
        if run.state == "running":
            run.wait(_wait_arg(arguments))
        return self._status(run)

    def author_review(self, arguments: dict[str, Any]) -> dict[str, Any]:
        run = self._run(arguments)
        request = run.pending
        if request is None:
            raise ToolError(f"run {run.run_id} has no atom awaiting review (state: {run.state})")
        if arguments.get("request_id") != request.request_id:
            raise ToolError(
                f"request_id {arguments.get('request_id')!r} is stale; the pending atom is "
                f"request_id {request.request_id}. Show that atom to the user first."
            )
        decision = arguments.get("decision")
        atom = request.atom
        if decision == "edit":
            edits = arguments.get("edits") or []
            if not edits:
                raise ToolError("edit needs at least one field=value entry in `edits`")
            for edit in edits:
                try:
                    atom = _apply_field_edit(atom, str(edit), request.edit_log)
                except ValueError as exc:
                    raise ToolError(f"edit rejected: {exc}") from exc
            request.atom = atom
            request.failed_checks_confirmed = False
            status = self._status(run)
            status["note"] = "Edit applied. Show the edited atom to the user and ask again."
            return status
        request.edit_log["review_channel"] = "mcp"
        if decision == "approve":
            if _approval_needs_failed_property_confirmation(
                atom,
                bool(arguments.get("confirm_failed_checks")),
            ):
                raise ToolError(
                    "This atom's symbolic checks failed. Tell the user which checks failed; "
                    "approve only if they still want it, with confirm_failed_checks=true."
                )
            reviewed = ReviewedAtom(
                atom=atom,
                decision=AtomDecision(
                    atom_name=atom.name,
                    action="approve",
                    intent_acknowledged_by_user=True,
                    symbolic_verified=getattr(atom, "symbolic_verified", False),
                    edit_delta=request.edit_log,
                ),
            )
        elif decision == "reject":
            reason = str(arguments.get("reason") or "").strip()
            if not reason:
                raise ToolError("reject needs the user's reason in `reason`")
            reviewed = ReviewedAtom(
                atom=atom,
                decision=AtomDecision(
                    atom_name=atom.name,
                    action="reject",
                    reason=reason,
                    edit_delta=request.edit_log,
                ),
            )
        else:
            raise ToolError("decision must be approve, reject or edit")
        run.resolve(request, reviewed)
        run.wait(_wait_arg(arguments))
        return self._status(run)

    def author_pause(self, arguments: dict[str, Any]) -> dict[str, Any]:
        run = self._run(arguments)
        if run.pending is None:
            raise ToolError(
                f"run {run.run_id} is not waiting for a review (state: {run.state}); "
                "a run can be paused only at a pending atom"
            )
        run.pause()
        run.thread.join(timeout=MAX_WAIT_SECONDS)
        return self._status(run)

    # -- helpers ------------------------------------------------------------

    def _run(self, arguments: dict[str, Any]) -> AuthoringRun:
        run_id = arguments.get("run_id")
        run = self.runs.get(run_id) if isinstance(run_id, str) else None
        if run is None:
            raise ToolError(f"unknown run_id: {run_id!r}")
        return run

    def _status(self, run: AuthoringRun) -> dict[str, Any]:
        status: dict[str, Any] = {
            "run_id": run.run_id,
            "state": run.state,
            "session_dir": str(run.session_dir) if run.session_dir else None,
            "recent_events": run.events[-8:],
        }
        request = run.pending
        if request is not None:
            status["state"] = "awaiting_review"
            status["pending_review"] = _render_pending(request)
        if run.state == "finished":
            status["result"] = _summarize_result(run.result)
        if run.error:
            status["error"] = run.error
        return status


def _default_pipeline_factory(
    *,
    spec_path: Path,
    out_dir: Path,
    resume_from: Optional[Path],
    schema_path: Optional[Path],
    session_id: Optional[str],
    provider: Optional[str],
    model: Optional[str],
    effort: Optional[str],
) -> Callable[[_McpReviewer], Any]:
    from autocedar.cli import _require_provider_auth, author_hooks
    from autocedar.llm import DEFAULT_EFFORT, LLMClient
    from autocedar.pipeline import author as author_pipeline
    from autocedar.providers import SessionOverrides, resolve_provider_config

    config = resolve_provider_config(
        session=SessionOverrides(provider=provider, model=model, reasoning_effort=effort),
    )
    try:
        _require_provider_auth(config.provider)
    except SystemExit as exc:
        raise ToolError(str(exc)) from exc
    llm = LLMClient(
        provider=config.provider,
        model=config.model,
        effort=config.reasoning_effort or DEFAULT_EFFORT,
    )

    def target(reviewer: _McpReviewer) -> Any:
        return author_pipeline(
            spec_path=spec_path,
            output_dir=out_dir,
            session_id=session_id,
            review_atom=reviewer,
            **author_hooks(llm, model=config.model, provider=config.provider),
            schema_path_override=str(schema_path) if schema_path else None,
            resume_from=resume_from,
            run_incremental_checks=False,
        )

    return target


# ---------------------------------------------------------------------------
# JSON-RPC over stdio.
# ---------------------------------------------------------------------------


class McpServer:
    """Minimal MCP server: initialize, tools/list, tools/call, ping."""

    def __init__(self, tools: Optional[AutoCedarTools] = None) -> None:
        self.tools = tools or AutoCedarTools()

    def handle(self, message: dict[str, Any]) -> Optional[dict[str, Any]]:
        method = message.get("method")
        msg_id = message.get("id")
        if msg_id is None:
            return None  # notification, e.g. notifications/initialized
        params = message.get("params") or {}
        try:
            result = self._dispatch(method, params)
        except _RpcError as exc:
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": exc.code, "message": str(exc)}}
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def _dispatch(self, method: Any, params: dict[str, Any]) -> dict[str, Any]:
        if method == "initialize":
            requested = params.get("protocolVersion")
            version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else SUPPORTED_PROTOCOL_VERSIONS[0]
            return {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "autocedar", "version": __version__},
                "instructions": SERVER_INSTRUCTIONS,
            }
        if method == "ping":
            return {}
        if method == "tools/list":
            return {"tools": self.tools.list_tools()}
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            try:
                payload = self.tools.call(str(name), arguments)
            except ToolError as exc:
                return _tool_result({"error": str(exc)}, is_error=True)
            except Exception as exc:  # noqa: BLE001 - surfaced to the agent
                detail = "".join(traceback.format_exception_only(type(exc), exc)).strip()
                return _tool_result({"error": detail}, is_error=True)
            return _tool_result(payload, is_error=False)
        if method in {"resources/list", "prompts/list"}:
            return {method.split("/")[0]: []}
        raise _RpcError(-32601, f"method not found: {method}")


class _RpcError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def _tool_result(payload: dict[str, Any], *, is_error: bool) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2, default=str)}],
        "isError": is_error,
    }


def serve_stdio(
    stdin: Optional[TextIO] = None,
    stdout: Optional[TextIO] = None,
    server: Optional[McpServer] = None,
) -> int:
    """Serve MCP over stdio until stdin closes.

    Pipeline code prints progress to stdout, which would corrupt the protocol
    stream, so ``sys.stdout`` is pointed at stderr while the server runs.
    """
    stdin = stdin or sys.stdin
    out = stdout or sys.stdout
    server = server or McpServer()
    saved_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
        for line in stdin:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError as exc:
                response: Optional[dict[str, Any]] = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"parse error: {exc}"},
                }
            else:
                response = server.handle(message) if isinstance(message, dict) else None
            if response is not None:
                out.write(json.dumps(response) + "\n")
                out.flush()
    finally:
        sys.stdout = saved_stdout
    return 0
