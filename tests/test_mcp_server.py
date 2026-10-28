"""Tests for ``autocedar.mcp_server``: the MCP protocol loop and the
agent-relayed review flow. The authoring pipeline is replaced by a scripted
target so no model or solver runs."""

from __future__ import annotations

import io
import json
import threading
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from autocedar.atoms import PropertyAtom
from autocedar.mcp_server import AutoCedarTools, McpServer, ToolError, serve_stdio


def _atom(name: str, *, failed: bool = False) -> PropertyAtom:
    return PropertyAtom(
        name=name,
        rationale="from R7",
        plain_english_summary=f"{name} summary",
        source_excerpt="Reviewers can read other reviews after submitting their own.",
        constraint_type="ceiling",
        action="readOtherReviews",
        principal_types=["User"],
        resource_types=["Submission"],
        reference_cedar=(
            'permit (principal is User, action == Action::"readOtherReviews", '
            "resource is Submission) when { resource.reviewersSubmitted.contains(principal) };"
        ),
        symbolic_verified=not failed,
        symbolic_verification_log=["satisfiable: FAILED"] if failed else ["satisfiable: ok"],
    )


@dataclass
class _FakeResult:
    session_dir: Path
    candidate_path: Path
    final_user_approved: bool = True
    notes: list[str] = field(default_factory=list)
    plan: object = None


def _factory(atoms, decisions, tmp_path: Path, gate: threading.Event | None = None):
    def factory(**kwargs):
        def target(reviewer):
            reviewer.begin_stage("Property review", len(atoms))
            for atom in atoms:
                decisions.append(reviewer(atom))
            if gate is not None:
                gate.wait(5)
            candidate = tmp_path / "candidate.cedar"
            candidate.write_text("permit (principal, action, resource);")
            return _FakeResult(session_dir=tmp_path, candidate_path=candidate)

        return target

    return factory


def _start(tools: AutoCedarTools, tmp_path: Path) -> dict:
    spec = tmp_path / "spec.md"
    spec.write_text("Reviewers can read other reviews after submitting their own.\n")
    return tools.author_start(
        {"spec_path": str(spec), "out_dir": str(tmp_path / "out"), "wait_seconds": 5},
    )


def test_review_flow_records_user_decisions(tmp_path: Path) -> None:
    decisions: list = []
    tools = AutoCedarTools(
        pipeline_factory=_factory([_atom("a1"), _atom("a2", failed=True), _atom("a3")], decisions, tmp_path),
    )
    status = _start(tools, tmp_path)
    run_id = status["run_id"]
    assert status["state"] == "awaiting_review"
    pending = status["pending_review"]
    assert pending["request_id"] == 1
    assert pending["name"] == "a1"
    assert "readOtherReviews" in pending["cedar"]

    with pytest.raises(ToolError, match="stale"):
        tools.author_review({"run_id": run_id, "request_id": 2, "decision": "approve"})

    status = tools.author_review(
        {"run_id": run_id, "request_id": 1, "decision": "approve", "wait_seconds": 5},
    )
    assert status["pending_review"]["name"] == "a2"
    assert status["pending_review"]["symbolic_verified"] is False

    with pytest.raises(ToolError, match="symbolic checks failed"):
        tools.author_review({"run_id": run_id, "request_id": 2, "decision": "approve"})
    status = tools.author_review(
        {
            "run_id": run_id,
            "request_id": 2,
            "decision": "approve",
            "confirm_failed_checks": True,
            "wait_seconds": 5,
        },
    )
    assert status["pending_review"]["name"] == "a3"

    status = tools.author_review(
        {
            "run_id": run_id,
            "request_id": 3,
            "decision": "edit",
            "edits": ["plain_english_summary=Only submitted reviewers read others"],
        },
    )
    assert status["pending_review"]["summary"] == "Only submitted reviewers read others"
    with pytest.raises(ToolError, match="reason"):
        tools.author_review({"run_id": run_id, "request_id": 3, "decision": "reject"})
    status = tools.author_review(
        {
            "run_id": run_id,
            "request_id": 3,
            "decision": "reject",
            "reason": "R7 also requires assignment",
            "wait_seconds": 5,
        },
    )
    assert status["state"] == "finished"
    assert status["result"]["completed"] is True
    assert "permit" in status["result"]["candidate_cedar"]

    actions = [r.decision.action for r in decisions]
    assert actions == ["approve", "approve", "reject"]
    assert decisions[0].decision.intent_acknowledged_by_user is True
    assert decisions[0].decision.edit_delta["review_channel"] == "mcp"
    assert decisions[2].decision.reason == "R7 also requires assignment"
    assert decisions[2].atom.plain_english_summary == "Only submitted reviewers read others"


def test_pause_stops_run_at_pending_atom(tmp_path: Path) -> None:
    decisions: list = []
    tools = AutoCedarTools(pipeline_factory=_factory([_atom("a1")], decisions, tmp_path))
    status = _start(tools, tmp_path)
    status = tools.author_pause({"run_id": status["run_id"]})
    assert status["state"] == "paused"
    assert status["session_dir"].startswith(str(tmp_path / "out" / "session-"))
    assert "resume" in status["error"].lower()
    assert decisions == []


def test_status_reports_running_while_pipeline_works(tmp_path: Path) -> None:
    gate = threading.Event()
    tools = AutoCedarTools(pipeline_factory=_factory([], [], tmp_path, gate=gate))
    spec = tmp_path / "spec.md"
    spec.write_text("Reviewers can read other reviews.\n")
    status = tools.author_start(
        {"spec_path": str(spec), "out_dir": str(tmp_path / "out"), "wait_seconds": 0.1},
    )
    assert status["state"] == "running"
    status = tools.author_status({"run_id": status["run_id"], "wait_seconds": 0.1})
    assert status["state"] == "running"
    gate.set()
    status = tools.author_status({"run_id": status["run_id"], "wait_seconds": 5})
    assert status["state"] == "finished"


def test_pipeline_errors_are_reported(tmp_path: Path) -> None:
    def factory(**kwargs):
        def target(reviewer):
            raise RuntimeError("schema failed to validate")

        return target

    tools = AutoCedarTools(pipeline_factory=factory)
    status = _start(tools, tmp_path)
    assert status["state"] == "error"
    assert "schema failed to validate" in status["error"]


def test_tool_argument_errors(tmp_path: Path) -> None:
    tools = AutoCedarTools(pipeline_factory=_factory([], [], tmp_path))
    with pytest.raises(ToolError, match="does not exist"):
        tools.author_start({"spec_path": str(tmp_path / "missing.md"), "out_dir": str(tmp_path)})
    with pytest.raises(ToolError, match="unknown run_id"):
        tools.author_status({"run_id": "nope"})
    with pytest.raises(ToolError, match="does not exist"):
        tools.verify({"workspace": str(tmp_path / "missing")})


def _rpc(server: McpServer, method: str, params: dict | None = None, msg_id: int = 1) -> dict:
    return server.handle({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params or {}})


def test_protocol_handshake_and_tool_listing() -> None:
    server = McpServer(AutoCedarTools(pipeline_factory=lambda **kw: None))
    init = _rpc(server, "initialize", {"protocolVersion": "2025-03-26", "capabilities": {}})
    assert init["result"]["protocolVersion"] == "2025-03-26"
    assert init["result"]["serverInfo"]["name"] == "autocedar"
    assert "never decide for them" in init["result"]["instructions"]
    unknown_version = _rpc(server, "initialize", {"protocolVersion": "1999-01-01"})
    assert unknown_version["result"]["protocolVersion"] == "2025-06-18"

    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    names = {t["name"] for t in _rpc(server, "tools/list")["result"]["tools"]}
    assert names == {"doctor", "verify", "author_start", "author_status", "author_review", "author_pause"}
    assert _rpc(server, "nope/method")["error"]["code"] == -32601

    bad = _rpc(server, "tools/call", {"name": "author_status", "arguments": {"run_id": "x"}})
    assert bad["result"]["isError"] is True
    assert "unknown run_id" in json.loads(bad["result"]["content"][0]["text"])["error"]


def test_serve_stdio_keeps_protocol_stream_clean() -> None:
    class PrintingTools(AutoCedarTools):
        def doctor(self, arguments):
            print("progress chatter that must not reach the protocol stream")
            return {"ok": True}

    tools = PrintingTools(pipeline_factory=lambda **kw: None)
    tools._by_name["doctor"].handler = tools.doctor
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "doctor", "arguments": {}}},
    ]
    stdin = io.StringIO("\n".join(json.dumps(r) for r in requests) + "\nnot json\n")
    stdout = io.StringIO()
    assert serve_stdio(stdin=stdin, stdout=stdout, server=McpServer(tools)) == 0
    lines = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert [line.get("id") for line in lines] == [1, 2, None]
    assert json.loads(lines[1]["result"]["content"][0]["text"]) == {"ok": True}
    assert lines[2]["error"]["code"] == -32700


def test_pending_map_and_permissions_question_offer_their_own_options() -> None:
    from autocedar.intent_map import IntentMap, MapScope, PermissionsQuestion
    from autocedar.mcp_server import _render_pending, _ReviewRequest

    intent_map = IntentMap(review_text="INTENT MAP\nScope s_release: ...")
    question = PermissionsQuestion(scopes=[MapScope("s_release", "release", "User", "WorkOrder", None)])

    shown_map = _render_pending(_ReviewRequest(request_id=1, atom=intent_map, stage="Intent map review", index=1, total=None))
    shown_question = _render_pending(_ReviewRequest(request_id=2, atom=question, stage="Intent map review", index=2, total=None))

    assert shown_map["kind"] == "intent_map"
    assert all("edit" not in option for option in shown_map["options"])
    assert "INTENT MAP" in shown_map["rendered"]
    assert shown_question["kind"] == "permissions_question"
    assert shown_question["options"][0].startswith("approve (yes")
    assert json.loads(shown_question["cedar"])["scopes"][0]["id"] == "s_release"
    assert "IS THE LIST OF PERMISSIONS COMPLETE?" in shown_question["rendered"]
