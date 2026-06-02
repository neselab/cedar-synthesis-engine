"""Tests for ``autocedar.corpus``.

Covers acceptance criterion 9 of ``docs/HITL_STEP_B_PLAN.md`` §9 —
session log directory layout including prose-excerpt-to-atom
attribution as a first-class field, and the
``intent_acknowledged_by_user`` vs ``symbolic_verified`` distinction.
"""

from __future__ import annotations

import json
from pathlib import Path

from autocedar.atoms import PropertyAtom
from autocedar.corpus import (
    AtomDecision,
    AttributionDecision,
    IterationLog,
    Session,
)


def test_session_creates_full_directory_layout(tmp_path: Path) -> None:
    s = Session("test-session", tmp_path)
    expected_subdirs = [
        "input",
        "stage1",
        "stage1_5",
        "stage1_75",
        "stage2",
        "stage2/final_plan",
        "stage2/final_plan/references",
        "stage2_5",
        "stage3",
        "stage3/iterations",
    ]
    for sub in expected_subdirs:
        assert (s.base / sub).is_dir(), f"missing subdir {sub}"


def test_attribution_decisions_are_first_class(tmp_path: Path) -> None:
    """§9.1 critical-field: prose-excerpt-to-atom attribution must be
    captured as its own JSON file with the span text and alternatives."""
    s = Session("test-session", tmp_path)
    decisions = [
        AttributionDecision(
            atom_name="careTeam_only_read",
            span_text="Doctors and nurses on the patient's care team can read records.",
            alternatives_considered=[
                "Doctors and nurses can read records.",
                "The owner can read.",
            ],
        ),
    ]
    s.write_stage2_attribution_decisions(decisions)
    path = s.base / "stage2" / "attribution_decisions.json"
    assert path.exists()
    parsed = json.loads(path.read_text())
    assert parsed[0]["atom_name"] == "careTeam_only_read"
    assert parsed[0]["span_text"].startswith("Doctors and nurses")
    assert len(parsed[0]["alternatives_considered"]) == 2
    assert parsed[0]["user_objected_to_attribution"] is False


def test_atom_decision_keeps_intent_and_symbolic_separate(tmp_path: Path) -> None:
    """§1.4 critical-field: intent_acknowledged_by_user must be a
    distinct field from symbolic_verified."""
    s = Session("test-session", tmp_path)
    decisions = [
        AtomDecision(
            atom_name="bad_atom",
            action="approve",
            intent_acknowledged_by_user=True,
            symbolic_verified=False,  # User approved despite a failed symbolic check.
        ),
        AtomDecision(
            atom_name="good_atom",
            action="approve",
            intent_acknowledged_by_user=True,
            symbolic_verified=True,
        ),
    ]
    s.write_stage2_decisions(decisions)
    parsed = json.loads((s.base / "stage2" / "decisions.json").read_text())
    bad = parsed[0]
    good = parsed[1]
    # Two separate keys.
    assert "intent_acknowledged_by_user" in bad
    assert "symbolic_verified" in bad
    # The bad case (approved despite symbolic failure) is captured.
    assert bad["intent_acknowledged_by_user"] is True
    assert bad["symbolic_verified"] is False


def test_iteration_log_keeps_verifier_and_critic_separate(tmp_path: Path) -> None:
    """§9.1: per-iteration logs keep verifier feedback and critic score
    in separate JSON files so corpus analysis can study disagreement."""
    s = Session("test-session", tmp_path)
    iter_log = IterationLog(
        iter_number=3,
        candidate_cedar="permit (...);",
        verifier_feedback={"passed": True, "checks": [{"name": "x", "passed": True}]},
        critic_score={"idiomatic": 4, "minimal": 4},
    )
    s.write_stage3_iteration(iter_log)
    iter_dir = s.base / "stage3" / "iterations" / "iter_3"
    assert (iter_dir / "candidate.cedar").read_text() == "permit (...);"
    assert (iter_dir / "verifier_feedback.json").exists()
    assert (iter_dir / "critic_score.json").exists()
    # The two are separate files (not merged).
    vf = json.loads((iter_dir / "verifier_feedback.json").read_text())
    cs = json.loads((iter_dir / "critic_score.json").read_text())
    assert vf["passed"] is True
    assert cs["idiomatic"] == 4


def test_transcript_flush_writes_chronological_event_log(tmp_path: Path) -> None:
    s = Session("test-session", tmp_path)
    s.write_input_spec("hello")
    s.write_stage1_proposed_atoms([])
    s.flush_transcript()
    path = s.base / "transcript.json"
    assert path.exists()
    events = json.loads(path.read_text())
    event_types = [e["event"] for e in events]
    assert "input.spec_written" in event_types
    assert "stage1.proposed" in event_types


def test_post_session_edits_are_appendable(tmp_path: Path) -> None:
    """The ``post_session_edits.json`` accumulates user edits made
    after the agent session closes."""
    s = Session("test-session", tmp_path)
    s.append_post_session_edit({"summary": "tightened admin gate", "diff": "..."})
    s.append_post_session_edit({"summary": "added audit annotation"})
    parsed = json.loads((s.base / "post_session_edits.json").read_text())
    assert len(parsed) == 2
    assert parsed[0]["summary"] == "tightened admin gate"
