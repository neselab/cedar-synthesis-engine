"""Tests for the Textual AutoCedar shell helpers."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from autocedar.tui import (
    AutoCedarApp,
    _describe_author_action,
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


def test_parse_author_args_defaults_and_options() -> None:
    options = parse_author_args([
        "spec.md",
        "--out",
        "runs",
        "--schema",
        "schema.cedarschema",
        "--session-id",
        "session-1",
        "--auto-approve",
    ])
    assert options.spec == Path("spec.md")
    assert options.out == Path("runs")
    assert options.schema == Path("schema.cedarschema")
    assert options.session_id == "session-1"
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


def test_natural_language_start_draft_request() -> None:
    intent = interpret_natural_language("start a policy draft", has_draft=False)
    assert intent.kind == "start_draft"


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
    system, messages = app._chat_request("can you atomize and verify a schema too?")
    user_context = messages[0]["content"]

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

    class FakeMessages:
        def stream(self, **kwargs):
            return FakeStream()

    class FakeClient:
        messages = FakeMessages()

    app = AutoCedarApp()
    events: list[tuple[str, str]] = []
    app.call_from_thread = lambda func, *args: func(*args)  # type: ignore[method-assign]
    app._make_anthropic_client = lambda: FakeClient()  # type: ignore[method-assign]
    app._start_stream_output = lambda: events.append(("start", ""))  # type: ignore[method-assign]
    app._update_stream_output = lambda text: events.append(("update", text))  # type: ignore[method-assign]
    app._finish_stream_output = lambda text: events.append(("finish", text))  # type: ignore[method-assign]

    answer = app._stream_chat_model("say hello")

    assert answer == "Hello"
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
