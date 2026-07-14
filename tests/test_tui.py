"""Tests for the Textual AutoCedar shell helpers."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Sequence

import pytest
from textual import events
from textual.widgets import ProgressBar

from autocedar.agent import AgentAction
from autocedar.atoms import EntityAtom, PropertyAtom
from autocedar.corpus import AtomDecision
from autocedar.tui import (
    AutoCedarApp,
    ClipboardResult,
    COMMANDS,
    CommandInput,
    HELP_TEXT,
    ReviewedAtom,
    TuiAtomReviewer,
    _describe_author_action,
    _draft_lines_from_text,
    _initial_model,
    _property_overview_text,
    _redact_sensitive_input,
    _render_cedar_for_review,
    _schema_overview_text,
    _slash_command_completion,
    _slash_command_palette_text,
    _split_review_input,
    _strip_rich_markup,
    parse_author_args,
    parse_synthesize_args,
    tokenize,
)
from autocedar.progress import format_property_progress


class FakePlanner:
    def __init__(self, action: AgentAction | Sequence[AgentAction]) -> None:
        self.actions = list(action) if isinstance(action, Sequence) else [action]
        self.calls: list[tuple[str, object]] = []

    def plan(self, user_input: str, state: object) -> AgentAction:
        self.calls.append((user_input, state))
        if len(self.actions) > 1:
            return self.actions.pop(0)
        return self.actions[0]


class _ImmediateReviewApp:
    def __init__(self) -> None:
        self.requests = []
        self.stage_events = []
        self.messages = []

    def call_from_thread(self, callback, *args):
        return callback(*args)

    def begin_review_stage(self, label: str, total: int | None) -> None:
        self.stage_events.append((label, total))

    def end_review_stage(self, label: str, approved: int, rejected: int) -> None:
        self.stage_events.append((label, approved, rejected))

    def begin_review(self, request) -> None:
        self.requests.append(request)
        request.result = ReviewedAtom(
            atom=request.current,
            decision=AtomDecision(
                atom_name=request.current.name,
                action="approve",
                symbolic_verified=True,
            ),
        )
        request.event.set()

    def _say(self, message: str) -> None:
        self.messages.append(message)

    def update_property_progress(self, payload) -> None:
        self.messages.append(format_property_progress(payload))


def test_tokenize_accepts_slash_commands_and_quotes() -> None:
    assert tokenize('/author "policy spec.md" --out runs') == [
        "author",
        "policy spec.md",
        "--out",
        "runs",
    ]


def test_initial_local_model_prefers_endpoint_specific_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "local")
    monkeypatch.setenv("AUTOCEDAR_LOCAL_MODEL", "served-local")
    monkeypatch.setenv("AUTOCEDAR_MODEL", "stale-cloud-model")

    assert _initial_model() == "served-local"


def test_setup_and_doctor_are_discoverable_in_tui_help() -> None:
    assert "setup" in COMMANDS
    assert "doctor" in COMMANDS
    assert "provider" in COMMANDS
    assert "models" in COMMANDS
    assert "export" in COMMANDS
    assert "inspect" in COMMANDS
    assert "search" in COMMANDS
    assert "/setup" in HELP_TEXT
    assert "/doctor" in HELP_TEXT
    assert "/provider" in HELP_TEXT
    assert "/models" in HELP_TEXT
    assert "/export" in HELP_TEXT
    assert "/inspect" in HELP_TEXT
    assert "/search" in HELP_TEXT


def test_tui_reviewer_property_counter_resets_after_schema_stage() -> None:
    app = _ImmediateReviewApp()
    reviewer = TuiAtomReviewer(app)  # type: ignore[arg-type]

    reviewer.begin_stage("Schema atom review", 2)
    reviewer(
        EntityAtom(
            name="User",
            rationale="user entity",
            plain_english_summary="Users exist.",
            source_excerpt="Users exist.",
        ),
    )
    reviewer(
        EntityAtom(
            name="Document",
            rationale="document entity",
            plain_english_summary="Documents exist.",
            source_excerpt="Documents exist.",
        ),
    )

    reviewer.begin_stage("Property intent review", None)
    reviewer(
        PropertyAtom(
            name="owner_can_view",
            rationale="owner view",
            plain_english_summary="Owners can view documents.",
            source_excerpt="The owner can view the document.",
            constraint_type="floor",
            action="view",
            principal_types=["User"],
            resource_types=["Document"],
            reference_cedar='permit(principal, action == Action::"view", resource);',
        ),
    )

    assert [request.index for request in app.requests] == [1, 2, 1]
    assert app.requests[-1].sequence == 3
    assert app.requests[-1].stage_label == "Property intent review"


def test_tui_reviewer_forwards_property_progress() -> None:
    app = _ImmediateReviewApp()
    reviewer = TuiAtomReviewer(app)  # type: ignore[arg-type]

    reviewer.property_progress(
        {
            "event": "source_start",
            "source_index": 2,
            "source_total": 5,
            "source_open": 4,
            "approved": 3,
            "decisions": 6,
        },
    )

    assert app.messages[-1] == (
        "source start | source 2/5 | open 4 | approved 3 | decisions 6"
    )


def test_tui_property_progress_bar_updates_from_payload() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            progress_bar = app.query_one("#property_progress_bar", ProgressBar)
            assert progress_bar.display is False

            app.update_property_progress(
                {
                    "event": "source_complete",
                    "source_total": 5,
                    "source_completed": 2,
                    "approved": 7,
                    "decisions": 8,
                },
            )
            await pilot.pause()

            assert progress_bar.display is True
            assert progress_bar.total == 5
            assert progress_bar.progress == 2

    asyncio.run(run())


def test_slash_command_palette_filters_commands() -> None:
    all_commands = _slash_command_palette_text("/")
    assert "/setup" in all_commands
    assert "/doctor" in all_commands
    assert "Tab completes" in all_commands

    filtered = _slash_command_palette_text("/se")
    assert "/setup" in filtered
    assert "/settings" in filtered
    assert "/doctor" not in filtered

    missing = _slash_command_palette_text("/zz")
    assert "No shortcut matches" in missing


def test_slash_command_completion_uses_first_palette_match() -> None:
    assert _slash_command_completion("/se") == "/setup "
    assert _slash_command_completion("/doctor") is None
    assert _slash_command_completion("doctor") is None
    assert _slash_command_completion("/zz") is None


def test_textual_tab_key_completes_focused_command_input() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            command = app.query_one("#command", CommandInput)
            command.value = "/se"
            command.cursor_position = len(command.value)
            await pilot.press("tab")
            await pilot.pause()
            assert command.value == "/setup "
            assert command.cursor_position == len("/setup ")
            await pilot.exit(None)

    asyncio.run(run())


def test_parse_author_args_defaults_and_options() -> None:
    options = parse_author_args([
        "spec.md",
        "--out",
        "runs",
        "--schema",
        "schema.cedarschema",
        "--session-id",
        "session-1",
        "--effort",
        "max",
        "--auto-approve",
    ])
    assert options.spec == Path("spec.md")
    assert options.out == Path("runs")
    assert options.schema == Path("schema.cedarschema")
    assert options.session_id == "session-1"
    assert options.effort == "max"
    assert options.auto_approve is True


def test_parse_author_args_rejects_unknown_option() -> None:
    with pytest.raises(ValueError, match="Unknown /author option"):
        parse_author_args(["spec.md", "--bad"])


def test_parse_synthesize_args_collects_scenarios_and_flags() -> None:
    options = parse_synthesize_args([
        "one",
        "two",
        "--out",
        "runs",
        "--max-iters",
        "7",
        "--no-review",
    ])
    assert options.scenarios == [Path("one"), Path("two")]
    assert options.out == Path("runs")
    assert options.max_iters == 7
    assert options.no_review is True


def test_split_review_input_supports_aliases_and_short_keys() -> None:
    assert _split_review_input("approve") == ("A", "")
    assert _split_review_input("reject too broad") == ("R", "too broad")
    assert _split_review_input("E name=User") == ("E", "name=User")


def test_schema_overview_extracts_entity_hierarchy_and_actions() -> None:
    overview = _schema_overview_text(
        """entity Person;

entity Doctor in [Person] {
    careTeam: Set<Patient>,
};

entity Record {
    patient: Patient,
};

action readRecord appliesTo {
    principal: [Doctor],
    resource: [Record],
    context: {
        now: datetime,
    },
};
""",
    )

    assert "Doctor in [Person]" in overview
    assert "careTeam: Set<Patient>" in overview
    assert "readRecord: [Doctor] -> [Record]" in overview
    assert "now: datetime" in overview


def test_property_overview_groups_by_action() -> None:
    overview = _property_overview_text([
        PropertyAtom(
            name="read_floor",
            rationale="doctor read",
            plain_english_summary="Doctors on the care team can read records.",
            source_excerpt="Doctors can read records.",
            constraint_type="floor",
            action="readRecord",
            principal_types=["Doctor"],
            resource_types=["Record"],
            reference_cedar='permit(principal, action == Action::"readRecord", resource);',
        ),
    ])

    assert "readRecord" in overview
    assert "FLOOR: [Doctor] -> [Record]" in overview
    assert "Doctors on the care team" in overview


def test_render_cedar_for_liveness_property_is_explanatory() -> None:
    atom = PropertyAtom(
        name="read_liveness",
        rationale="non-empty permission",
        plain_english_summary="At least one read request is permitted.",
        source_excerpt="Doctors can read records.",
        constraint_type="liveness",
        action="readRecord",
        principal_types=["Doctor"],
        resource_types=["Record"],
    )

    preview = _render_cedar_for_review(atom)

    assert "Liveness property" in preview
    assert "unknown atom kind" not in preview


def test_natural_language_without_api_key_requires_live_planner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = AutoCedarApp()
    messages: list[str] = []
    app._say = messages.append  # type: ignore[method-assign]

    app._handle_natural_language_input("start a policy draft")

    assert app.pending_action is None
    assert app.draft_lines == []
    assert "Natural-language control needs the live agent planner" in messages[0]


def test_draft_mode_routes_requirements_through_planner() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        planner = FakePlanner(
            AgentAction(
                kind="append_requirements",
                content="Doctors can read records for patients on their care team.",
            ),
        )
        app.agent_planner_factory = lambda: planner
        async with app.run_test() as pilot:
            app._start_drafting()
            app._submit_command_text("Doctors can read records for patients on their care team.")
            await pilot.pause()
            assert app.draft_lines == [
                "Doctors can read records for patients on their care team.",
            ]
            assert [call[0] for call in planner.calls] == [
                "Doctors can read records for patients on their care team.",
            ]
            await pilot.exit(None)

    asyncio.run(run())


def test_sensitive_input_redaction() -> None:
    assert _redact_sensitive_input("/apikey sk-ant-secret123") == "/apikey [redacted-api-key]"
    assert (
        _redact_sensitive_input("ANTHROPIC_API_KEY=sk-ant-secret123")
        == "ANTHROPIC_API_KEY=[redacted]"
    )


def test_textual_app_mounts() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            assert app.query_one("#command")
            assert app.query_one("#brand")
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_gates_plain_english_before_draft_capture() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        app.agent_planner_factory = lambda: FakePlanner(AgentAction(kind="start_draft"))
        async with app.run_test() as pilot:
            app._handle_shell_input("Doctors can read assigned patient records.")
            await pilot.pause()
            assert app.draft_lines == []
            assert app.drafting_active is False
            assert app.pending_action is not None
            app._handle_confirmation_input("yes")
            assert app.draft_lines == []
            assert app.drafting_active is True
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_does_not_capture_mode_trigger_as_requirement() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        planner = FakePlanner([
            AgentAction(kind="start_draft"),
            AgentAction(
                kind="append_requirements",
                content="The owner of a document can both view and edit it.",
            ),
        ])
        app.agent_planner_factory = lambda: planner
        async with app.run_test() as pilot:
            app._handle_shell_input("A policy and a schema from a bunch of nl requirements I have")
            await pilot.pause()
            assert app.pending_action is not None
            app._handle_confirmation_input("yes")
            assert app.drafting_active is True
            assert app.draft_lines == []
            app._handle_shell_input("The owner of a document can both view and edit it.")
            await pilot.pause()
            assert app.draft_lines == [
                "The owner of a document can both view and edit it.",
            ]
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_appends_policy_text_after_drafting_is_active() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        app.agent_planner_factory = lambda: FakePlanner(
            AgentAction(
                kind="append_requirements",
                content="Doctors can read assigned patient records.",
            ),
        )
        async with app.run_test() as pilot:
            app._start_drafting()
            app._handle_shell_input("Doctors can read assigned patient records.")
            await pilot.pause()
            assert app.pending_action is None
            assert app.draft_lines == [
                "Doctors can read assigned patient records.",
            ]
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_appends_schema_setup_statement_after_drafting_is_active() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        app.agent_planner_factory = lambda: FakePlanner(
            AgentAction(
                kind="append_requirements",
                content="A document management system has Users and Documents.",
            ),
        )
        async with app.run_test() as pilot:
            app._start_drafting()
            app._handle_shell_input("A document management system has Users and Documents.")
            await pilot.pause()
            assert app.pending_action is None
            assert app.draft_lines == [
                "A document management system has Users and Documents.",
            ]
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_appends_multiline_paste_after_drafting_is_active() -> None:
    requirements = """\
The new system will allow students to register for courses and view report cards from personal computers attached to the campus LAN.

At the beginning of each semester, students may request a course catalogue containing a list of course offerings for the semester.

Students cannot register for course offerings after registration for the current semester has been closed.

Only Professors can enter grades for students.
"""

    async def run() -> None:
        app = AutoCedarApp()
        app.agent_planner_factory = lambda: FakePlanner(
            AgentAction(kind="append_requirements", content=requirements),
        )
        async with app.run_test() as pilot:
            app._start_drafting()
            app._handle_shell_input(requirements)
            await pilot.pause()
            assert app.pending_action is None
            assert app.draft_lines == [
                "The new system will allow students to register for courses and view report cards from personal computers attached to the campus LAN.",
                "At the beginning of each semester, students may request a course catalogue containing a list of course offerings for the semester.",
                "Students cannot register for course offerings after registration for the current semester has been closed.",
                "Only Professors can enter grades for students.",
            ]
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_command_input_paste_forwards_all_requirement_lines() -> None:
    requirements = """\
The new system will allow students to register for courses and view report cards from personal computers attached to the campus LAN.

At the beginning of each semester, students may request a course catalogue containing a list of course offerings for the semester.

Information about each course, such as professor, department, and prerequisites, will be included to help students make informed decisions.

Students must be able to access the system during this time to add or drop courses.

At the end of the semester, the student will be able to access the system to view an electronic report card.

This use case allows a Student to register for course offerings in the current semester.

The Student can also update or delete course selections if changes are made within the add or drop period at the beginning of the semester.

The Student may update the course selections on the current selection by deleting and adding new course offerings.

Students cannot register for course offerings after registration for the current semester has been closed.

This use case allows a Student to view his or her report card for the previously completed semester.

Professors must be able to access the on-line system to indicate which courses they will be teaching.

They will also need to see which students signed up for their course offerings.

In addition, the professors will be able to record the grades for the students in each class.

This use case allows a Professor to select the course offerings from the course catalog for the courses that he or she is eligible for and wishes to teach in the upcoming semester.

If there is no conflict, the system updates the course offering information for each offering the professor selects (i.e., records the professor as the instructor for the course offering).

Professors cannot change the course offerings they teach after registration for the current semester has been closed.

This use case allows a Professor to submit student grades for one or more classes completed in the previous semester.

The system retrieves a list of all students who were registered for the course offering.

For each student on the list, the Professor enters a grade: A, B, C, D, F, or I. The system records the student’s grade for the course offering.

Only the Registrar is allowed to change any student information.

This use case allows a Registrar to close the registration process.

Since student grades are sensitive information, the system must employ extra security measures to prevent unauthorized access.

The system must prevent students from changing any schedules other than their own, and professors from modifying assigned course offerings for other professors.

Only Professors can enter grades for students.
"""

    async def run() -> None:
        app = AutoCedarApp()
        app.agent_planner_factory = lambda: FakePlanner(
            AgentAction(kind="append_requirements", content=requirements),
        )
        async with app.run_test() as pilot:
            app._submit_command_text("/draft")
            assert app.drafting_active is True
            command = app.query_one("#command", CommandInput)
            command._on_paste(events.Paste(requirements))
            await pilot.pause()
            assert len(app.draft_lines) == 24
            assert app.draft_lines[0].startswith("The new system will allow students")
            assert app.draft_lines[-1] == "Only Professors can enter grades for students."
            assert command.value == ""
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_keeps_complaint_out_of_active_draft() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        app.agent_planner_factory = lambda: FakePlanner(
            AgentAction(kind="respond", message="I understand; the draft is unchanged."),
        )
        async with app.run_test() as pilot:
            app._start_drafting()
            app._handle_shell_input("I said start a policy draft, you said it was active.")
            assert app.draft_lines == []
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_plus_prefix_forces_draft_capture() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._handle_shell_input("+ A document management system has Users and Documents.")
            assert app.drafting_active is True
            assert app.draft_lines == [
                "A document management system has Users and Documents.",
            ]
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_clear_draft_disables_drafting() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._start_drafting()
            app._append_draft_text("Doctors can read assigned patient records.")
            assert app.drafting_active is True
            app._clear_draft()
            assert app.draft_lines == []
            assert app.drafting_active is False
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_clear_it_while_drafting_requests_draft_clear() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        app.agent_planner_factory = lambda: FakePlanner(AgentAction(kind="clear_draft"))
        async with app.run_test() as pilot:
            app._start_drafting()
            app._handle_shell_input("clear it")
            await pilot.pause()
            assert app.pending_action is not None
            app._handle_confirmation_input("yes")
            assert app.draft_lines == []
            assert app.drafting_active is False
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_delete_draft_while_drafting_requests_draft_clear() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        app.agent_planner_factory = lambda: FakePlanner(AgentAction(kind="clear_draft"))
        async with app.run_test() as pilot:
            app._start_drafting()
            app._append_draft_text("Doctors can read assigned patient records.")
            app._handle_shell_input("I want to delete the draft")
            await pilot.pause()
            assert app.draft_lines == ["Doctors can read assigned patient records."]
            assert app.pending_action is not None
            app._handle_confirmation_input("yes")
            assert app.draft_lines == []
            assert app.drafting_active is False
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_clear_draft_command_requests_draft_clear() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._start_drafting()
            app._append_draft_text("Doctors can read assigned patient records.")
            app._handle_command_input("/clear draft")
            assert app.pending_action is not None
            app._handle_confirmation_input("yes")
            assert app.draft_lines == []
            assert app.drafting_active is False
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_draft_edit_command_replaces_line() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app.draft_lines = [
                "Doctors can read records.",
                "Nurses can update vitals.",
            ]
            app._handle_command_input("/draft edit 2 Nurses can update vitals only during their shift.")
            assert app.draft_lines == [
                "Doctors can read records.",
                "Nurses can update vitals only during their shift.",
            ]
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_draft_delete_command_removes_line() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app.draft_lines = [
                "Doctors can read records.",
                "This line should go.",
                "Patients can view their own records.",
            ]
            app._handle_command_input("/draft delete 2")
            assert app.draft_lines == [
                "Doctors can read records.",
                "Patients can view their own records.",
            ]
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_natural_language_draft_edit_goes_through_planner() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        planner = FakePlanner(
            AgentAction(
                kind="edit_draft",
                mode="set_line",
                line=2,
                value="Nurses can update vitals only during their shift.",
            ),
        )
        app.agent_planner_factory = lambda: planner
        async with app.run_test() as pilot:
            app.draft_lines = [
                "Doctors can read records.",
                "Nurses can update vitals.",
            ]
            app._handle_shell_input("change line 2 to Nurses can update vitals only during their shift")
            await pilot.pause()
            assert [call[0] for call in planner.calls] == [
                "change line 2 to Nurses can update vitals only during their shift",
            ]
            assert app.draft_lines == [
                "Doctors can read records.",
                "Nurses can update vitals only during their shift.",
            ]
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_draft_command_starts_capture_mode() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._handle_command_input("/draft")
            assert app.drafting_active is True
            assert app.draft_lines == []
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_clear_transcript_does_not_clear_draft() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._start_drafting()
            app._append_draft_text("Doctors can read assigned patient records.")
            app._handle_command_input("/clear")
            assert app.draft_lines == ["Doctors can read assigned patient records."]
            assert app.drafting_active is True
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_author_current_draft_is_real_action_not_chat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    async def run() -> None:
        app = AutoCedarApp()
        started: list[Path] = []
        planner = FakePlanner([
            AgentAction(
                kind="append_requirements",
                content="The owner of a document can view it.",
            ),
            AgentAction(kind="author_current_draft", spec=str(Path("autocedar-spec.md"))),
        ])
        app.agent_planner_factory = lambda: planner
        async with app.run_test() as pilot:
            app._start_author = lambda options: started.append(options.spec)  # type: ignore[method-assign]
            app._submit_command_text("/draft")
            app._submit_command_text("The owner of a document can view it.")
            await pilot.pause()
            app._submit_command_text("Ok let's author")
            await pilot.pause()
            assert app.pending_action is not None
            assert "HITL authoring" in app.pending_action.summary
            app._submit_command_text("yes")
            assert started == [Path("autocedar-spec.md")]
            assert Path("autocedar-spec.md").read_text() == (
                "The owner of a document can view it.\n"
            )
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_slash_author_without_args_uses_current_draft(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    async def run() -> None:
        app = AutoCedarApp()
        started: list[Path] = []
        async with app.run_test() as pilot:
            app._start_author = lambda options: started.append(options.spec)  # type: ignore[method-assign]
            app.draft_lines = ["The owner of a document can view it."]
            app._submit_command_text("/author")
            assert app.pending_action is not None
            app._submit_command_text("yes")
            assert started == [Path("autocedar-spec.md")]
            assert Path("autocedar-spec.md").read_text() == (
                "The owner of a document can view it.\n"
            )
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_slash_author_option_only_args_use_current_draft(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    async def run() -> None:
        app = AutoCedarApp()
        started: list[tuple[Path, Path, str | None]] = []
        async with app.run_test() as pilot:
            app._start_author = (
                lambda options: started.append((options.spec, options.out, options.session_id))
            )  # type: ignore[method-assign]
            app.draft_lines = ["The owner of a document can view it."]
            app._submit_command_text(
                "/author --out runs --session-id draft-session --model claude-opus-4-7",
            )
            assert app.pending_action is not None
            app._submit_command_text("yes")
            assert started == [(Path("autocedar-spec.md"), Path("runs"), "draft-session")]
            assert Path("autocedar-spec.md").read_text() == (
                "The owner of a document can view it.\n"
            )
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_show_the_draft_uses_buffer_not_chat() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        shown: list[bool] = []
        app.agent_planner_factory = lambda: FakePlanner(AgentAction(kind="show_draft"))
        async with app.run_test() as pilot:
            app._start_drafting()
            app.draft_lines = ["Doctors can read assigned patient records."]
            app._show_draft = lambda: shown.append(True)  # type: ignore[method-assign]
            app._submit_command_text("show the draft")
            await pilot.pause()
            assert shown == [True]
            await pilot.exit(None)

    asyncio.run(run())


def test_tui_registers_latest_authoring_artifacts(tmp_path: Path) -> None:
    app = AutoCedarApp()
    session = tmp_path / "session"
    schema = session / "stage1" / "final_schema.cedarschema"
    candidate = session / "scenario" / "candidate.cedar"
    schema.parent.mkdir(parents=True)
    candidate.parent.mkdir(parents=True)
    schema.write_text("entity User;")
    candidate.write_text("permit(principal, action, resource);")

    app._register_authoring_artifacts(session, candidate, schema_override=None)

    assert app.latest_session_dir == session
    assert app.latest_schema_path == schema
    assert app.latest_policy_path == candidate


def test_tui_records_authoring_validation_status_from_eval_log(tmp_path: Path) -> None:
    app = AutoCedarApp()
    session = tmp_path / "session"
    schema = session / "stage1" / "final_schema.cedarschema"
    candidate = session / "harness_runs" / "scenario" / "candidate.cedar"
    eval_log = session / "harness_runs" / "scenario" / "eval_log.json"
    schema.parent.mkdir(parents=True)
    candidate.parent.mkdir(parents=True)
    schema.write_text("entity User;")
    candidate.write_text("permit(principal, action, resource);")
    eval_log.write_text(
        '{"converged": true, "iterations": 1, "final_loss": 0, "checks_total": 6, "error": ""}',
    )
    app._update_status = lambda: None  # type: ignore[method-assign]

    app._register_authoring_artifacts(session, candidate, schema_override=None)
    app._record_authoring_result(True)
    state = app._agent_state()

    assert app.latest_candidate_validated is True
    assert app.latest_synthesis_converged is True
    assert app.latest_synthesis_iterations == 1
    assert app.latest_synthesis_loss == 0
    assert "passed all 6 recorded checks" in app.latest_status_summary
    assert state.latest_authoring_complete is True
    assert state.latest_candidate_validated is True
    assert state.latest_policy_exists is True
    assert state.latest_schema_exists is True


def test_tui_planner_receives_pre_planning_workflow_state(tmp_path: Path) -> None:
    async def run() -> None:
        app = AutoCedarApp()
        policy = tmp_path / "candidate.cedar"
        schema = tmp_path / "schema.cedarschema"
        policy.write_text("permit(principal, action, resource);")
        schema.write_text("entity User;")
        planner = FakePlanner(AgentAction(kind="export_artifacts"))
        app.agent_planner_factory = lambda: planner
        async with app.run_test() as pilot:
            app.latest_session_dir = tmp_path
            app.latest_policy_path = policy
            app.latest_schema_path = schema
            app.latest_authoring_complete = True
            app.latest_authoring_approved = True
            app.latest_candidate_validated = True
            app.latest_synthesis_converged = True
            app.latest_synthesis_iterations = 1
            app.latest_synthesis_loss = 0
            app.latest_status_summary = "Candidate passed all recorded checks in 1 iteration(s)."
            app._export_artifacts = lambda path=None: None  # type: ignore[method-assign]

            app._submit_command_text("can you export it")
            await pilot.pause()

            assert planner.calls
            _, state = planner.calls[0]
            assert state.active_task == "idle"
            assert state.busy is False
            assert state.latest_authoring_complete is True
            assert state.latest_candidate_validated is True
            assert state.latest_policy_exists is True
            assert state.latest_schema_exists is True
            assert any(tool["action"] == "export_artifacts" for tool in state.tools)
            assert any(tool["action"] == "inspect_workflow" for tool in state.tools)
            assert any(tool["action"] == "search_artifacts" for tool in state.tools)
            await pilot.exit(None)

    asyncio.run(run())


def test_tui_artifact_slash_commands_dispatch_to_latest_paths(tmp_path: Path) -> None:
    app = AutoCedarApp()
    schema = tmp_path / "schema.cedarschema"
    policy = tmp_path / "candidate.cedar"
    app.latest_schema_path = schema
    app.latest_policy_path = policy
    calls: list[tuple[Path | None, str]] = []
    app._show_file_artifact = lambda path, label: calls.append((path, label))  # type: ignore[method-assign]

    app._handle_command_input("/schema")
    app._handle_command_input("/policy")

    assert calls == [(schema, "Cedar schema"), (policy, "Cedar policy")]


def test_tui_inspect_workflow_reads_generated_status(tmp_path: Path) -> None:
    app = AutoCedarApp()
    session = tmp_path / "session"
    schema = session / "stage1" / "final_schema.cedarschema"
    policy = session / "harness_runs" / "scenario" / "candidate.cedar"
    eval_log = session / "harness_runs" / "scenario" / "eval_log.json"
    schema.parent.mkdir(parents=True)
    policy.parent.mkdir(parents=True)
    schema.write_text("entity User;\n")
    policy.write_text("permit(principal, action == Action::\"view\", resource);\n")
    eval_log.write_text(
        '{"converged": true, "iterations": 1, "final_loss": 0, "checks_total": 3, "error": ""}',
    )
    app._update_status = lambda: None  # type: ignore[method-assign]
    app._register_authoring_artifacts(session, policy, schema_override=None)
    app._record_authoring_result(True)
    writes: list[object] = []
    app._write = writes.append  # type: ignore[method-assign]

    app._handle_command_input("/inspect passed")

    text = "\n".join(str(getattr(item, "renderable", item)) for item in writes)
    assert "candidate validated[/]: True" in text
    assert "Candidate passed all 3 recorded checks" in text
    assert "eval_log.json" in text


def test_tui_search_artifacts_finds_generated_text(tmp_path: Path) -> None:
    app = AutoCedarApp()
    session = tmp_path / "session"
    policy = session / "harness_runs" / "scenario" / "candidate.cedar"
    policy.parent.mkdir(parents=True)
    policy.write_text("permit(principal, action == Action::\"editDocument\", resource);\n")
    app.latest_session_dir = session
    app.latest_policy_path = policy
    writes: list[object] = []
    app._write = writes.append  # type: ignore[method-assign]

    app._handle_command_input("/search editDocument")

    text = "\n".join(str(getattr(item, "renderable", item)) for item in writes)
    assert "candidate.cedar:1" in text
    assert "editDocument" in text


def test_tui_copy_session_uses_clipboard_helper(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    app = AutoCedarApp()
    app.latest_session_dir = tmp_path / "session"
    copied: list[str] = []
    messages: list[str] = []
    monkeypatch.setattr(
        "autocedar.tui._copy_to_clipboard",
        lambda text: copied.append(text) or ClipboardResult(True, "ok"),
    )
    app._say = messages.append  # type: ignore[method-assign]

    app._handle_command_input("/copy session")

    assert copied == [str(tmp_path / "session")]
    assert any("Copied session path" in message for message in messages)


def test_tui_export_artifacts_writes_stable_files(tmp_path: Path) -> None:
    app = AutoCedarApp()
    schema = tmp_path / "run" / "stage1" / "final_schema.cedarschema"
    policy = tmp_path / "run" / "stage3" / "final_candidate.cedar"
    schema.parent.mkdir(parents=True)
    policy.parent.mkdir(parents=True)
    schema.write_text("entity User;\n")
    policy.write_text("permit(principal, action, resource);\n")
    app.latest_session_dir = tmp_path / "run"
    app.latest_schema_path = schema
    app.latest_policy_path = policy
    app.latest_authoring_complete = True
    app.latest_authoring_approved = True
    app.latest_candidate_validated = True
    app.latest_synthesis_converged = True
    app.latest_synthesis_iterations = 1
    app.latest_synthesis_loss = 0
    app.latest_status_summary = "Candidate passed all 2 recorded checks in 1 iteration(s)."
    app.copyable_transcript = ["you > author this", "autocedar > Authoring complete."]
    app._write = lambda content: None  # type: ignore[method-assign]

    export_dir = tmp_path / "exported"
    app._handle_command_input(f"/export {export_dir}")

    assert (export_dir / "schema.cedarschema").read_text() == "entity User;\n"
    assert (export_dir / "policy_store.cedar").read_text() == (
        "permit(principal, action, resource);\n"
    )
    assert "author this" in (export_dir / "transcript.txt").read_text()
    index = (export_dir / "artifacts.txt").read_text()
    assert f"session={tmp_path / 'run'}" in index
    assert f"schema={schema}" in index
    assert f"policy={policy}" in index
    assert "candidate_validated=True" in index
    assert "status=Candidate passed all 2 recorded checks" in index


def test_tui_copy_last_and_transcript_use_plain_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = AutoCedarApp()
    copied: list[str] = []
    messages: list[str] = []
    monkeypatch.setattr(
        "autocedar.tui._copy_to_clipboard",
        lambda text: copied.append(text) or ClipboardResult(True, "ok"),
    )
    app._write = lambda content: None  # type: ignore[method-assign]
    app._say("Policy authoring has [bold]started[/].")
    app.copyable_transcript.append("you > Owners can edit documents.")
    app._say = messages.append  # type: ignore[method-assign]

    app._handle_command_input("/copy last")
    app._handle_command_input("/copy transcript")

    assert copied[0] == "Policy authoring has started."
    assert "autocedar > Policy authoring has started." in copied[1]
    assert "you > Owners can edit documents." in copied[1]
    assert any("Copied last assistant message" in message for message in messages)
    assert any("Copied transcript" in message for message in messages)


def test_strip_rich_markup_for_copy_buffer() -> None:
    assert _strip_rich_markup("[bold #f0c678]Hello[/] [dim]there[/]") == "Hello there"


def test_draft_lines_from_text_filters_blank_lines() -> None:
    assert _draft_lines_from_text("A\n\n B \n") == ["A", "B"]


def test_tui_natural_language_show_schema_routes_to_artifact_command() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        planner = FakePlanner(AgentAction(kind="show_schema"))
        calls: list[Sequence[str]] = []
        app.agent_planner_factory = lambda: planner
        async with app.run_test() as pilot:
            app._show_schema_command = lambda args: calls.append(args)  # type: ignore[method-assign]
            app._submit_command_text("show the schema")
            await pilot.pause()
            assert calls == [[]]
            assert planner.calls
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_state_snapshot_includes_drafting_and_pending_action() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        app.agent_planner_factory = lambda: FakePlanner(AgentAction(kind="start_draft"))
        async with app.run_test() as pilot:
            app._handle_shell_input("Doctors can read assigned patient records.")
            await pilot.pause()
            state = app._state_snapshot()
            assert "drafting: off" in state
            assert "draft lines: 0" in state
            assert "pending confirmation:" in state
            assert "clean spec/schema inputs" in state
            await pilot.exit(None)

    asyncio.run(run())


def test_author_confirmation_describes_schema_mode() -> None:
    no_schema = parse_author_args(["spec.md", "--out", "runs"])
    with_schema = parse_author_args([
        "spec.md",
        "--out",
        "runs",
        "--schema",
        "schema.cedarschema",
    ])

    assert "propose schema atoms" in _describe_author_action(no_schema, from_draft=False)
    assert "bounded local Stage 2 property bundles" in _describe_author_action(no_schema, from_draft=False)
    assert "skip Stage 1 schema atomization" in _describe_author_action(with_schema, from_draft=False)
    assert "bounded local Stage 2 property bundles" in _describe_author_action(with_schema, from_draft=False)


def test_textual_settings_commands_update_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AUTOCEDAR_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_CHAT_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_AUTHOR_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_EFFORT", raising=False)
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    validated: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "autocedar.tui.validate_anthropic_api_key",
        lambda value, *, model: validated.append((value, model)),
    )

    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._handle_command_input("/model claude-sonnet-4-6")
            assert app.llm_model == "claude-sonnet-4-6"
            assert os.environ["AUTOCEDAR_MODEL"] == "claude-sonnet-4-6"

            app._handle_command_input("/effort max")
            assert app.llm_effort == "max"
            assert os.environ["AUTOCEDAR_EFFORT"] == "max"

            app._handle_command_input("/effort xhigh")
            assert app.llm_effort == "max"

            app._handle_command_input("/apikey sk-ant-secret123")
            assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-secret123"
            assert app.active_api_key == "sk-ant-secret123"
            assert validated == [("sk-ant-secret123", "claude-sonnet-4-6")]
            env_path = tmp_path / "config" / ".env"
            assert env_path.read_text() == "ANTHROPIC_API_KEY=sk-ant-secret123\n"

            app._handle_command_input("/apikey status")

            app._handle_command_input("/apikey clear")
            assert "ANTHROPIC_API_KEY" not in os.environ
            assert app.active_api_key == ""
            assert env_path.read_text() == ""
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_provider_and_models_commands_use_codex_bridge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "anthropic")
    monkeypatch.delenv("AUTOCEDAR_MODEL", raising=False)
    monkeypatch.setattr("autocedar.tui.codex_auth_available", lambda: True)

    class FakeRuntimeInfo:
        auth_available = True
        provider = "openai-codex"
        model = "gpt-5.5"
        base_url = "https://chatgpt.com/backend-api/codex"
        auth_source = "/tmp/codex/auth.json"
        models = ["gpt-5.5", "gpt-5.4"]
        thinking_efforts = ("low", "medium", "high", "max")
        model_details = [
            type("Model", (), {
                "slug": "gpt-5.5",
                "display_name": "GPT-5.5",
                "supported_reasoning_levels": (
                    ("low", "Fast responses with lighter reasoning"),
                    ("xhigh", "Extra high reasoning depth"),
                ),
                "default_reasoning_level": "medium",
                "context_window": 272000,
                "max_context_window": 272000,
                "service_tiers": ("Fast",),
                "speed_tiers": ("fast",),
                "default_verbosity": "low",
                "support_verbosity": True,
                "supports_reasoning_summaries": True,
            })(),
            type("Model", (), {
                "slug": "gpt-5.4",
                "display_name": "GPT-5.4",
                "supported_reasoning_levels": (("medium", ""),),
                "default_reasoning_level": "medium",
                "context_window": 272000,
                "max_context_window": 1000000,
                "service_tiers": (),
                "speed_tiers": (),
                "default_verbosity": "medium",
                "support_verbosity": True,
                "supports_reasoning_summaries": True,
            })(),
        ]
        error = None

    monkeypatch.setattr("autocedar.tui.codex_runtime_info", lambda: FakeRuntimeInfo())

    async def run() -> None:
        app = AutoCedarApp()
        written: list[object] = []

        def capture(content: object) -> None:
            written.append(getattr(content, "renderable", content))

        async with app.run_test() as pilot:
            app._write = capture  # type: ignore[method-assign]
            app._handle_command_input("/provider codex")
            assert app.llm_provider == "codex"
            assert app.llm_model == "gpt-5.5"
            assert os.environ["AUTOCEDAR_PROVIDER"] == "codex"

            app._handle_command_input("/models")

            rendered = "\n".join(str(item) for item in written)
            assert "gpt-5.5" in rendered
            assert "gpt-5.4" in rendered
            assert "openai-codex" in rendered
            assert "max (Extra high reasoning depth)" in rendered
            assert "Fast" in rendered
            assert "272,000 default, 1,000,000 max" in rendered
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_provider_and_models_commands_use_local_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "codex")
    monkeypatch.setenv("AUTOCEDAR_LOCAL_MODEL", "autocedar-local")

    class FakeRuntimeInfo:
        available = True
        base_url = "http://127.0.0.1:8000/v1"
        models = ["autocedar-local", "backup-local"]
        error = None

    monkeypatch.setattr("autocedar.tui.openai_runtime_info", lambda: FakeRuntimeInfo())

    async def run() -> None:
        app = AutoCedarApp()
        written: list[object] = []

        def capture(content: object) -> None:
            written.append(getattr(content, "renderable", content))

        async with app.run_test() as pilot:
            app._write = capture  # type: ignore[method-assign]
            app._handle_command_input("/provider local")
            assert app.llm_provider == "local"
            assert app.llm_model == "autocedar-local"
            assert os.environ["AUTOCEDAR_PROVIDER"] == "local"

            app._handle_command_input("/models")

            rendered = "\n".join(str(item) for item in written)
            assert "autocedar-local" in rendered
            assert "backup-local" in rendered
            assert "127.0.0.1:8000" in rendered

            app._handle_command_input("/model local-v2")
            assert app.llm_model == "local-v2"
            assert os.environ["AUTOCEDAR_LOCAL_MODEL"] == "local-v2"

            app._handle_command_input("/provider codex")
            assert app.llm_provider == "codex"
            assert app.llm_model.startswith("gpt-")

            app._handle_command_input("/provider local")
            assert app.llm_provider == "local"
            assert app.llm_model == "local-v2"

            monkeypatch.setattr(
                "autocedar.tui.openai_runtime_info",
                lambda: (_ for _ in ()).throw(
                    AssertionError("status updates must not make network probes"),
                ),
            )
            app._update_status()
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_apikey_rejects_invalid_key_before_saving(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))

    class AuthenticationError(Exception):
        pass

    def fail_validation(value: str, *, model: str) -> None:
        _ = value, model
        raise AuthenticationError("invalid x-api-key")

    monkeypatch.setattr("autocedar.tui.validate_anthropic_api_key", fail_validation)

    async def run() -> None:
        app = AutoCedarApp()
        written: list[str] = []
        async with app.run_test() as pilot:
            app._say = written.append  # type: ignore[method-assign]
            app._write = written.append  # type: ignore[method-assign]
            app._handle_command_input("/apikey sk-ant-invalid123")
            assert "ANTHROPIC_API_KEY" not in os.environ
            assert not (tmp_path / "config" / ".env").exists()
            assert any("did not save" in item for item in written)
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_apikey_rejects_redacted_placeholder_without_live_validation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    validation_calls: list[str] = []
    monkeypatch.setattr(
        "autocedar.tui.validate_anthropic_api_key",
        lambda value, *, model: validation_calls.append(value),
    )

    async def run() -> None:
        app = AutoCedarApp()
        written: list[str] = []
        async with app.run_test() as pilot:
            app._say = written.append  # type: ignore[method-assign]
            app._write = written.append  # type: ignore[method-assign]
            app._handle_command_input("/apikey [redacted-api-key]")
            assert "ANTHROPIC_API_KEY" not in os.environ
            assert not (tmp_path / "config" / ".env").exists()
            assert validation_calls == []
            assert any("redacted value" in item for item in written)
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_apikey_normalizes_pasted_key_before_saving(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    validated: list[str] = []
    monkeypatch.setattr(
        "autocedar.tui.validate_anthropic_api_key",
        lambda value, *, model: validated.append(value),
    )

    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._say = lambda message: None  # type: ignore[method-assign]
            app._handle_command_input('/apikey "sk-ant-\u200bsecret 123"')
            assert validated == ["sk-ant-secret123"]
            assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-secret123"
            assert (tmp_path / "config" / ".env").read_text() == (
                "ANTHROPIC_API_KEY=sk-ant-secret123\n"
            )
            await pilot.exit(None)

    asyncio.run(run())


def test_make_anthropic_client_receives_resolved_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env123")
    captured: list[str | None] = []

    class FakeAnthropicModule:
        class Anthropic:
            def __init__(self, *, api_key: str | None = None) -> None:
                captured.append(api_key)

    monkeypatch.setitem(sys.modules, "anthropic", FakeAnthropicModule)

    app = AutoCedarApp()
    app.active_api_key = "sk-ant-active123"
    app._make_anthropic_client()

    assert captured == ["sk-ant-active123"]


def test_runtime_settings_resolve_author_and_synthesis_defaults() -> None:
    app = AutoCedarApp()
    app.llm_model = "claude-selected"
    app.llm_effort = "max"

    author = app._resolve_author_options(parse_author_args(["spec.md"]))
    assert author.model == "claude-selected"
    assert author.effort == "max"

    synth = app._resolve_synthesize_options(parse_synthesize_args(["scenario"]))
    assert synth.phase1_model == "claude-selected"
    assert synth.phase2_model == "claude-selected"


def test_speaker_label_is_autocedar() -> None:
    app = AutoCedarApp()
    written: list[str] = []
    app._write = written.append  # type: ignore[method-assign]

    app._say("hello")

    assert "[bold #f0c678]autocedar[/]" in written[0]
    assert "[bold #f0c678]cedar[/]" not in written[0]


def test_textual_activity_indicator_updates_while_busy() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            stream = app.query_one("#stream")
            app._start_activity("authoring")
            assert stream.display is True
            first = app.activity_frame
            app._tick_activity()
            second = app.activity_frame
            assert app.activity_message == "authoring"
            assert first != second
            app._stop_activity()
            assert stream.display is False
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_busy_blocks_premature_review_or_slash_commands() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        written: list[str] = []
        async with app.run_test() as pilot:
            app._say = written.append  # type: ignore[method-assign]
            app.busy = True
            app.active_task = "author autocedar-spec.md"
            app.pending_review = None
            app._submit_command_text("/author")
            app._submit_command_text("A")
            assert any("still working" in item for item in written)
            assert all("Usage: /author" not in item for item in written)
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_does_not_store_greeting_as_draft_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._handle_shell_input("Hey")
            assert app.draft_lines == []
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_requires_confirmation_before_natural_language_verify(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    async def run() -> None:
        app = AutoCedarApp()
        app.agent_planner_factory = lambda: FakePlanner(
            AgentAction(kind="verify_workspace", workspace="workspace"),
        )
        async with app.run_test() as pilot:
            app._handle_shell_input("verify the workspace")
            await pilot.pause()
            assert app.pending_action is not None
            assert app.busy is False
            app._handle_confirmation_input("no")
            assert app.pending_action is None
            assert app.busy is False
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_confirmation_runs_only_after_yes() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        ran: list[str] = []
        async with app.run_test() as pilot:
            app._request_confirmation("Run test action.", lambda: ran.append("yes"))
            assert ran == []
            app._handle_confirmation_input("yes")
            assert ran == ["yes"]
            await pilot.exit(None)

    asyncio.run(run())
