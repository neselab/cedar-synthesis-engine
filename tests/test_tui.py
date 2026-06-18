"""Tests for the Textual AutoCedar shell helpers."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Sequence

import pytest

from autocedar.atoms import PropertyAtom
from autocedar.tui import (
    AutoCedarApp,
    ClipboardResult,
    COMMANDS,
    HELP_TEXT,
    _describe_author_action,
    _property_overview_text,
    _redact_sensitive_input,
    _render_cedar_for_review,
    _schema_overview_text,
    _split_review_input,
    interpret_natural_language,
    parse_author_args,
    parse_synthesize_args,
    tokenize,
)


def test_tokenize_accepts_slash_commands_and_quotes() -> None:
    assert tokenize('/author "policy spec.md" --out runs') == [
        "author",
        "policy spec.md",
        "--out",
        "runs",
    ]


def test_setup_and_doctor_are_discoverable_in_tui_help() -> None:
    assert "setup" in COMMANDS
    assert "doctor" in COMMANDS
    assert "/setup" in HELP_TEXT
    assert "/doctor" in HELP_TEXT


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


def test_natural_language_verify_workspace() -> None:
    intent = interpret_natural_language("verify the workspace", has_draft=False)
    assert intent.kind == "verify"
    assert intent.workspace == Path("workspace")


def test_natural_language_save_draft_path() -> None:
    intent = interpret_natural_language("save this as policy.md", has_draft=True)
    assert intent.kind == "save_draft"
    assert intent.path == Path("policy.md")


def test_natural_language_author_current_draft_with_schema() -> None:
    intent = interpret_natural_language(
        "author this with schema workspace/schema.cedarschema",
        has_draft=True,
    )
    assert intent.kind == "author"
    assert intent.from_draft is True
    assert intent.author_options is not None
    assert intent.author_options.spec == Path("autocedar-spec.md")
    assert intent.author_options.schema == Path("workspace/schema.cedarschema")


def test_natural_language_author_parses_model_output_and_review_mode() -> None:
    intent = interpret_natural_language(
        "author spec.md with schema workspace/schema.cedarschema output runs model claude-opus session id demo auto approve",
        has_draft=False,
    )
    assert intent.kind == "author"
    assert intent.author_options is not None
    assert intent.author_options.spec == Path("spec.md")
    assert intent.author_options.schema == Path("workspace/schema.cedarschema")
    assert intent.author_options.out == Path("runs")
    assert intent.author_options.model == "claude-opus"
    assert intent.author_options.session_id == "demo"
    assert intent.author_options.auto_approve is True


def test_natural_language_policy_text_requests_draft_capture() -> None:
    intent = interpret_natural_language(
        "Doctors can read records for patients on their care team.",
        has_draft=False,
    )
    assert intent.kind == "append_draft"


def test_natural_language_schema_setup_statement_requests_draft_capture() -> None:
    intent = interpret_natural_language(
        "A document management system has Users and Documents.",
        has_draft=False,
    )

    assert intent.kind == "append_draft"


def test_natural_language_start_draft_request() -> None:
    intent = interpret_natural_language("start a policy draft", has_draft=False)
    assert intent.kind == "start_draft"


def test_natural_language_show_the_draft_request() -> None:
    intent = interpret_natural_language("show the draft", has_draft=True)
    assert intent.kind == "show_draft"


def test_natural_language_runtime_status_routes_to_chat() -> None:
    intent = interpret_natural_language("are you drafting?", has_draft=False)
    assert intent.kind == "message"


def test_natural_language_greeting_is_not_added_to_draft() -> None:
    intent = interpret_natural_language("Hey", has_draft=False)
    assert intent.kind == "message"


def test_natural_language_ambiguous_short_reply_is_not_added_to_draft() -> None:
    intent = interpret_natural_language("really?", has_draft=False)
    assert intent.kind == "message"


def test_natural_language_spec_schema_question_is_answered() -> None:
    intent = interpret_natural_language("Just the spec or the schema too?", has_draft=False)
    assert intent.kind == "message"


def test_natural_language_schema_atomization_question_uses_chat_context() -> None:
    intent = interpret_natural_language(
        "can you atomize and verify a schema too?",
        has_draft=False,
    )

    assert intent.kind == "message"
    assert "Stage 1 schema atomization" not in intent.message


def test_natural_language_question_is_not_added_to_draft() -> None:
    intent = interpret_natural_language("what can you do for me?", has_draft=False)
    assert intent.kind == "message"
    intent = interpret_natural_language("why is this failing?", has_draft=True)
    assert intent.kind == "message"


def test_natural_language_clear_it_clears_existing_draft() -> None:
    intent = interpret_natural_language("clear it", has_draft=True)
    assert intent.kind == "clear_draft"


def test_natural_language_synthesize_scenario() -> None:
    intent = interpret_natural_language(
        "synthesize emergency_break_glass no review max iters 7 output runs run id trial phase1 model opus phase2 model haiku generate references",
        has_draft=False,
    )
    assert intent.kind == "synthesize"
    assert intent.synthesize_options is not None
    assert intent.synthesize_options.scenarios == [
        Path("cedarbench/scenarios/realworld/emergency_break_glass"),
    ]
    assert intent.synthesize_options.no_review is True
    assert intent.synthesize_options.max_iters == 7
    assert intent.synthesize_options.out == Path("runs")
    assert intent.synthesize_options.run_id == "trial"
    assert intent.synthesize_options.phase1_model == "opus"
    assert intent.synthesize_options.phase2_model == "haiku"
    assert intent.synthesize_options.gen_references is True


def test_natural_language_settings_updates() -> None:
    intent = interpret_natural_language("set model to claude-sonnet-4-6", has_draft=False)
    assert intent.kind == "settings"
    assert intent.settings_update is not None
    assert intent.settings_update.model == "claude-sonnet-4-6"

    intent = interpret_natural_language("use effort max", has_draft=False)
    assert intent.kind == "settings"
    assert intent.settings_update is not None
    assert intent.settings_update.effort == "max"

    intent = interpret_natural_language("set api key sk-ant-secret123", has_draft=False)
    assert intent.kind == "settings"
    assert intent.settings_update is not None
    assert intent.settings_update.api_key == "sk-ant-secret123"


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
        async with app.run_test() as pilot:
            app._handle_shell_input("Doctors can read assigned patient records.")
            assert app.draft_lines == []
            assert app.drafting_active is False
            assert app.pending_action is not None
            app._handle_confirmation_input("yes")
            assert app.draft_lines == [
                "Doctors can read assigned patient records.",
            ]
            assert app.drafting_active is True
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_appends_policy_text_after_drafting_is_active() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._start_drafting()
            app._handle_shell_input("Doctors can read assigned patient records.")
            assert app.pending_action is None
            assert app.draft_lines == [
                "Doctors can read assigned patient records.",
            ]
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_appends_schema_setup_statement_after_drafting_is_active() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._start_drafting()
            app._handle_shell_input("A document management system has Users and Documents.")
            assert app.pending_action is None
            assert app.draft_lines == [
                "A document management system has Users and Documents.",
            ]
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_keeps_complaint_out_of_active_draft() -> None:
    async def run() -> None:
        app = AutoCedarApp()
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
            app._start_drafting("Doctors can read assigned patient records.")
            assert app.drafting_active is True
            app._clear_draft()
            assert app.draft_lines == []
            assert app.drafting_active is False
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_clear_it_while_drafting_requests_draft_clear() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._start_drafting()
            app._handle_shell_input("clear it")
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
            app._start_drafting("Doctors can read assigned patient records.")
            app._handle_command_input("/clear draft")
            assert app.pending_action is not None
            app._handle_confirmation_input("yes")
            assert app.draft_lines == []
            assert app.drafting_active is False
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
            app._start_drafting("Doctors can read assigned patient records.")
            app._handle_command_input("/clear")
            assert app.draft_lines == ["Doctors can read assigned patient records."]
            assert app.drafting_active is True
            await pilot.exit(None)

    asyncio.run(run())


def test_textual_app_show_the_draft_uses_buffer_not_chat() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        shown: list[bool] = []
        async with app.run_test() as pilot:
            app._start_drafting("Doctors can read assigned patient records.")
            app._show_draft = lambda: shown.append(True)  # type: ignore[method-assign]
            app._start_chat_response = (  # type: ignore[method-assign]
                lambda raw, fallback: (_ for _ in ()).throw(AssertionError("chat should not handle draft display"))
            )
            app._handle_shell_input("show the draft")
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


def test_tui_natural_language_show_schema_routes_to_artifact_command() -> None:
    app = AutoCedarApp()
    calls: list[Sequence[str]] = []
    app._show_schema_command = lambda args: calls.append(args)  # type: ignore[method-assign]

    app._handle_shell_input("show the schema")

    assert calls == [[]]


def test_textual_app_state_snapshot_includes_drafting_and_pending_action() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._handle_shell_input("Doctors can read assigned patient records.")
            state = app._state_snapshot()
            assert "drafting: off" in state
            assert "draft lines: 0" in state
            assert "pending confirmation:" in state
            assert "clean spec/schema inputs" in state
            await pilot.exit(None)

    asyncio.run(run())


def test_chat_request_includes_backend_process_and_tui_context() -> None:
    app = AutoCedarApp()
    app.llm_model = "claude-test"
    app.llm_effort = "max"
    system, messages = app._chat_request("can you atomize and verify a schema too?")
    user_context = messages[0]["content"]

    assert "model: claude-test" in user_context
    assert "effort: max" in user_context
    assert "process context" in user_context
    assert "Stage 1 schema atomization" in user_context
    assert "HITL review" in user_context
    assert "Stage 2 property atoms" in user_context
    assert "symbolically verifies each atom" in user_context
    assert "TUI legend context" in user_context
    assert "HITL means human-in-the-loop review" in user_context
    assert "Do not invent capabilities" in system


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
    assert "Stage 2 property atoms" in _describe_author_action(no_schema, from_draft=False)
    assert "skip Stage 1 schema atomization" in _describe_author_action(with_schema, from_draft=False)
    assert "Stage 2 property atoms" in _describe_author_action(with_schema, from_draft=False)


def test_textual_settings_commands_update_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AUTOCEDAR_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_CHAT_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_AUTHOR_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_EFFORT", raising=False)

    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._handle_command_input("/model claude-sonnet-4-6")
            assert app.llm_model == "claude-sonnet-4-6"
            assert os.environ["AUTOCEDAR_MODEL"] == "claude-sonnet-4-6"

            app._handle_command_input("/effort max")
            assert app.llm_effort == "max"
            assert os.environ["AUTOCEDAR_EFFORT"] == "max"

            app._handle_command_input("/apikey sk-ant-secret123")
            assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-secret123"

            app._handle_command_input("/apikey clear")
            assert "ANTHROPIC_API_KEY" not in os.environ
            await pilot.exit(None)

    asyncio.run(run())


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


def test_local_chat_response_answers_identity_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = AutoCedarApp()

    answer = app._local_chat_response("are you an llm?", fallback="fallback")

    assert "Anthropic chat model" in answer
    assert "fallback" not in answer


def test_local_chat_response_admits_prior_fallback_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = AutoCedarApp()

    answer = app._local_chat_response("you didn't answer my question", fallback="fallback")

    assert "fallback response" in answer


def test_speaker_label_is_autocedar() -> None:
    app = AutoCedarApp()
    written: list[str] = []
    app._write = written.append  # type: ignore[method-assign]

    app._say("hello")

    assert "[bold #f0c678]autocedar[/]" in written[0]
    assert "[bold #f0c678]cedar[/]" not in written[0]


def test_stream_chat_model_emits_incremental_text() -> None:
    class FakeStream:
        text_stream = ["Hel", "lo"]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    seen_kwargs = {}

    class FakeMessages:
        def stream(self, **kwargs):
            seen_kwargs.update(kwargs)
            return FakeStream()

    class FakeClient:
        messages = FakeMessages()

    app = AutoCedarApp()
    app.llm_model = "claude-test"
    app.llm_effort = "max"
    events: list[tuple[str, str]] = []
    app.call_from_thread = lambda func, *args: func(*args)  # type: ignore[method-assign]
    app._make_anthropic_client = lambda: FakeClient()  # type: ignore[method-assign]
    app._start_stream_output = lambda: events.append(("start", ""))  # type: ignore[method-assign]
    app._update_stream_output = lambda text: events.append(("update", text))  # type: ignore[method-assign]
    app._finish_stream_output = lambda text: events.append(("finish", text))  # type: ignore[method-assign]

    answer = app._stream_chat_model("say hello")

    assert answer == "Hello"
    assert seen_kwargs["model"] == "claude-test"
    assert seen_kwargs["output_config"] == {"effort": "max"}
    assert events == [
        ("start", ""),
        ("update", "Hel"),
        ("update", "Hello"),
        ("finish", "Hello"),
    ]


def test_answer_chat_uses_streaming_when_api_key_is_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    app = AutoCedarApp()
    said: list[str] = []
    finished: list[bool] = []
    app.call_from_thread = lambda func, *args: func(*args)  # type: ignore[method-assign]
    app._stream_chat_model = lambda raw: "streamed answer"  # type: ignore[method-assign]
    app._say = said.append  # type: ignore[method-assign]
    app._finish_task = lambda: finished.append(True)  # type: ignore[method-assign]

    app._answer_chat("are you there?", fallback="fallback")

    assert app.chat_history == [("are you there?", "streamed answer")]
    assert said == []
    assert finished == [True]


def test_stream_output_mounts_and_clears() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            stream = app.query_one("#stream")
            assert stream.display is False
            app._start_stream_output()
            assert stream.display is True
            app._update_stream_output("Hello")
            app._finish_stream_output("Hello")
            assert stream.display is False
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


def test_textual_app_requires_confirmation_before_natural_language_verify() -> None:
    async def run() -> None:
        app = AutoCedarApp()
        async with app.run_test() as pilot:
            app._handle_shell_input("verify the workspace")
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
