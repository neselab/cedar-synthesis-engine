"""Tests for AutoCedar's structured terminal-agent control plane."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from autocedar.agent import AgentAction, AgentPlanResponse, AgentState, ProviderAgentPlanner


def test_agent_action_rejects_unknown_tool_kind() -> None:
    with pytest.raises(ValidationError):
        AgentAction.model_validate({"kind": "pretend_authoring_started"})


def test_agent_state_prompt_json_includes_pending_context() -> None:
    state = AgentState(
        active_task="idle",
        busy=False,
        drafting_active=True,
        draft_line_count=2,
        draft_excerpt=["Users can view documents.", "Owners can edit documents."],
        pending_confirmation="none",
        pending_review="Property review: owner_can_edit",
        tools=[{"action": "inspect_workflow", "slash": "/inspect", "description": "inspect"}],
        api_key_set=True,
    )

    text = state.to_prompt_json()

    assert '"drafting_active": true' in text
    assert "owner_can_edit" in text
    assert "Owners can edit documents." in text
    assert "inspect_workflow" in text


def test_provider_agent_planner_returns_structured_action() -> None:
    class FakeMessages:
        def parse(self, **kwargs):
            assert kwargs["output_format"] is AgentPlanResponse
            assert "terminal-agent planner" in kwargs["system"]
            return SimpleNamespace(
                parsed_output=AgentPlanResponse(
                    action=AgentAction(kind="author_current_draft", spec="autocedar-spec.md"),
                ),
            )

    planner = ProviderAgentPlanner(
        client=SimpleNamespace(messages=FakeMessages()),
        model="claude-test",
        effort="high",
    )
    action = planner.plan(
        "ok let's author",
        AgentState(
            active_task="idle",
            busy=False,
            drafting_active=True,
            draft_line_count=1,
            draft_excerpt=["Owners can view documents."],
            api_key_set=True,
        ),
    )

    assert action.kind == "author_current_draft"
    assert action.spec == "autocedar-spec.md"


def test_provider_agent_planner_json_retry_handles_parse_timeout() -> None:
    class FakeMessages:
        def parse(self, **kwargs):
            _ = kwargs
            raise RuntimeError("grammar compilation timed out")

        def create(self, **kwargs):
            assert "JSON Schema" in kwargs["messages"][0]["content"]
            return SimpleNamespace(
                content=[
                    SimpleNamespace(
                        type="text",
                        text='{"action": {"kind": "show_draft"}}',
                    ),
                ],
            )

    planner = ProviderAgentPlanner(
        client=SimpleNamespace(messages=FakeMessages()),
        model="claude-test",
        effort="high",
    )

    action = planner.plan(
        "show the draft",
        AgentState(active_task="idle", busy=False, drafting_active=True, draft_line_count=1),
    )

    assert action.kind == "show_draft"
