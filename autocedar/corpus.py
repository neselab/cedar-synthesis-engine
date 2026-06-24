"""Session log writer (corpus plumbing).

See ``docs/HITL_STEP_B_PLAN.md`` §9.1 for the required directory layout
and the load-bearing fields. Use of the captured corpus (fine-tuning,
autocurriculum, regression testing) is out of scope for v1; the
plumbing is in scope so the data accumulates from day one.

Critical fields the log captures, that we cannot recover later:

- Per atom: the prose excerpt the agent attached AND the alternative
  excerpts it considered. (``attribution_decisions.json``.)
- Per user decision: ``intent_acknowledged_by_user`` separate from
  ``symbolic_verified`` — distinct keys in ``decisions.json``.
- Per Stage 3 iteration: both verifier feedback AND critic score,
  separately stored.
"""

from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from autocedar.atoms import (
    PropertyAtom,
    SchemaDraft,
    VerificationPlanDraft,
    to_dict,
)


# ---------------------------------------------------------------------------
# Attribution log entry — first-class per §9.1.
# ---------------------------------------------------------------------------

@dataclass
class AttributionDecision:
    """One agent decision about which prose span generated this atom.

    The ``span_text`` is what the agent attached as ``source_excerpt``;
    ``alternatives_considered`` is the (possibly empty) list of other
    spans the agent thought about and rejected. Cheap to capture now,
    expensive to retrofit per the §9.1 critical-field comment.
    """

    atom_name: str
    span_text: str
    alternatives_considered: list[str] = field(default_factory=list)
    user_objected_to_attribution: bool = False


# ---------------------------------------------------------------------------
# Decision log entry.
# ---------------------------------------------------------------------------

@dataclass
class AtomDecision:
    """A user's review decision on a single atom.

    Per §1.4 / §9.1, ``intent_acknowledged_by_user`` and
    ``symbolic_verified`` are deliberately separate fields so we can
    later study where users approved despite imperfect grounding —
    the most valuable training signal for improving the agent's
    prose-translation accuracy.
    """

    atom_name: str
    action: str  # "approve" | "reject" | "edit" | "question"
    reason: str = ""
    edit_delta: dict[str, Any] = field(default_factory=dict)
    intent_acknowledged_by_user: bool = False
    symbolic_verified: bool = False


# ---------------------------------------------------------------------------
# Iteration log entry.
# ---------------------------------------------------------------------------

@dataclass
class IterationLog:
    """One Stage 3 iteration: candidate + verifier feedback + critic score.

    These three fields are kept separate per §9.1 so corpus analysis
    can study how often verifier and critic agree on convergence.
    """

    iter_number: int
    candidate_cedar: str
    verifier_feedback: dict[str, Any] = field(default_factory=dict)
    critic_score: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Session — top-level corpus writer.
# ---------------------------------------------------------------------------

class Session:
    """Writes the per-session corpus layout under a base directory.

    Directory layout matches §9.1 of HITL_STEP_B_PLAN.md exactly.
    The ``transcript.json`` is the canonical flattened event log;
    every per-stage write also appends a structured event entry to it.
    """

    def __init__(self, session_id: str, base_dir: str | Path) -> None:
        self.session_id = session_id
        self.base = Path(base_dir) / session_id
        self.base.mkdir(parents=True, exist_ok=True)
        (self.base / "input").mkdir(exist_ok=True)
        (self.base / "stage1").mkdir(exist_ok=True)
        (self.base / "stage1_5").mkdir(exist_ok=True)
        (self.base / "stage1_75").mkdir(exist_ok=True)
        (self.base / "stage2").mkdir(exist_ok=True)
        (self.base / "stage2" / "final_plan").mkdir(exist_ok=True)
        (self.base / "stage2" / "final_plan" / "references").mkdir(exist_ok=True)
        (self.base / "stage2_5").mkdir(exist_ok=True)
        (self.base / "stage3").mkdir(exist_ok=True)
        (self.base / "stage3" / "iterations").mkdir(exist_ok=True)
        self._events: list[dict[str, Any]] = []

    # -----------------------------------------------------------------
    # Input.
    # -----------------------------------------------------------------

    def write_input_spec(self, spec_text: str, filename: str = "policy_spec.md") -> None:
        (self.base / "input" / filename).write_text(spec_text)
        self._event("input.spec_written", {"filename": filename, "size": len(spec_text)})

    # -----------------------------------------------------------------
    # Stage 1.
    # -----------------------------------------------------------------

    def write_stage1_proposed_atoms(self, atoms: list[Any]) -> None:
        path = self.base / "stage1" / "proposed_atoms.json"
        path.write_text(json.dumps([to_dict(a) for a in atoms], indent=2))
        self._event("stage1.proposed", {"count": len(atoms)})

    def write_stage1_attribution_decisions(
        self, decisions: list[AttributionDecision],
    ) -> None:
        path = self.base / "stage1" / "attribution_decisions.json"
        path.write_text(json.dumps([to_dict(d) for d in decisions], indent=2))
        self._event("stage1.attributions_logged", {"count": len(decisions)})

    def write_stage1_decisions(self, decisions: list[AtomDecision]) -> None:
        path = self.base / "stage1" / "decisions.json"
        path.write_text(json.dumps([to_dict(d) for d in decisions], indent=2))
        self._event("stage1.decisions_logged", {"count": len(decisions)})

    def write_stage1_final_schema(self, schema_text: str) -> None:
        (self.base / "stage1" / "final_schema.cedarschema").write_text(schema_text)
        self._event("stage1.schema_written", {"size": len(schema_text)})

    def write_stage1_schema_validation(self, attempts: list[dict[str, Any]]) -> None:
        path = self.base / "stage1" / "schema_validation.json"
        path.write_text(json.dumps(attempts, indent=2))
        self._event("stage1.schema_validation", {"attempts": len(attempts)})

    # -----------------------------------------------------------------
    # Stage 1.5 — schema amendments forced by Stage 2 sugars.
    # -----------------------------------------------------------------

    def write_stage1_5_amendments(self, amendments: list[dict[str, Any]]) -> None:
        path = self.base / "stage1_5" / "amendments.json"
        path.write_text(json.dumps(amendments, indent=2))
        self._event("stage1_5.amendments", {"count": len(amendments)})

    def write_stage1_5_schema_gaps(self, gaps: list[dict[str, Any]]) -> None:
        path = self.base / "stage1_5" / "schema_gaps.json"
        path.write_text(json.dumps(gaps, indent=2))
        self._event("stage1_5.schema_gaps", {"count": len(gaps)})

    def write_stage1_5_schema_gap_repairs(self, repairs: list[dict[str, Any]]) -> None:
        path = self.base / "stage1_5" / "schema_gap_repairs.json"
        path.write_text(json.dumps(repairs, indent=2))
        self._event("stage1_5.schema_gap_repairs", {"count": len(repairs)})

    # -----------------------------------------------------------------
    # Stage 2.
    # -----------------------------------------------------------------

    def write_stage2_proposed_atoms(self, atoms: list[PropertyAtom]) -> None:
        path = self.base / "stage2" / "proposed_atoms.json"
        path.write_text(json.dumps([to_dict(a) for a in atoms], indent=2))
        self._event("stage2.proposed", {"count": len(atoms)})

    def write_stage2_attribution_decisions(
        self, decisions: list[AttributionDecision],
    ) -> None:
        path = self.base / "stage2" / "attribution_decisions.json"
        path.write_text(json.dumps([to_dict(d) for d in decisions], indent=2))
        self._event("stage2.attributions_logged", {"count": len(decisions)})

    def write_stage2_decisions(self, decisions: list[AtomDecision]) -> None:
        path = self.base / "stage2" / "decisions.json"
        path.write_text(json.dumps([to_dict(d) for d in decisions], indent=2))
        self._event("stage2.decisions_logged", {"count": len(decisions)})

    def write_stage2_critic_reviews(self, reviews: list[dict[str, Any]]) -> None:
        path = self.base / "stage2" / "critic_reviews.json"
        path.write_text(json.dumps(reviews, indent=2))
        self._event("stage2.critic_reviews", {"count": len(reviews)})

    def write_stage2_intent_graph(self, graph: dict[str, Any]) -> None:
        path = self.base / "stage2" / "intent_graph.json"
        path.write_text(json.dumps(graph, indent=2))
        summary = graph.get("summary", {})
        self._event("stage2.intent_graph", summary if isinstance(summary, dict) else {})

    def write_stage2_symbolic_verification_logs(
        self, logs: dict[str, list[str]],
    ) -> None:
        path = self.base / "stage2" / "symbolic_verification_logs.json"
        path.write_text(json.dumps(logs, indent=2))
        self._event("stage2.verification_logged", {"atom_count": len(logs)})

    def write_stage2_adversarial_examples(
        self, examples_per_atom: dict[str, list[dict[str, Any]]],
    ) -> None:
        path = self.base / "stage2" / "adversarial_examples.json"
        path.write_text(json.dumps(examples_per_atom, indent=2))
        self._event(
            "stage2.adversarial_examples",
            {"atom_count": len(examples_per_atom)},
        )

    def write_stage2_final_plan(
        self, plan_py_text: str, references: dict[str, str],
    ) -> None:
        plan_dir = self.base / "stage2" / "final_plan"
        (plan_dir / "verification_plan.py").write_text(plan_py_text)
        for name, cedar in references.items():
            (plan_dir / "references" / f"{name}.cedar").write_text(cedar)
        self._event(
            "stage2.plan_written",
            {"reference_count": len(references)},
        )

    # -----------------------------------------------------------------
    # Stage 1.75 — pre-Stage-3 unsat detection.
    # -----------------------------------------------------------------

    def write_stage1_75_unsat_core(self, unsat: bool, core: list[str], detail: str) -> None:
        path = self.base / "stage1_75" / "unsat_core.json"
        path.write_text(json.dumps({"unsat": unsat, "core": core, "detail": detail}, indent=2))
        self._event("stage1_75.consistency_check", {"unsat": unsat, "core": core})

    # -----------------------------------------------------------------
    # Stage 3 — per-iteration logs.
    # -----------------------------------------------------------------

    def write_stage3_iteration(self, iteration: IterationLog) -> None:
        d = self.base / "stage3" / "iterations" / f"iter_{iteration.iter_number}"
        d.mkdir(exist_ok=True)
        (d / "candidate.cedar").write_text(iteration.candidate_cedar)
        (d / "verifier_feedback.json").write_text(
            json.dumps(iteration.verifier_feedback, indent=2),
        )
        (d / "critic_score.json").write_text(
            json.dumps(iteration.critic_score, indent=2),
        )
        self._event(
            "stage3.iteration",
            {
                "iter": iteration.iter_number,
                "verifier_passed": iteration.verifier_feedback.get("passed", False),
                "critic_mean": iteration.critic_score.get("composite_mean"),
            },
        )

    def write_stage3_final_candidate(self, candidate_text: str) -> None:
        (self.base / "stage3" / "final_candidate.cedar").write_text(candidate_text)
        self._event("stage3.final_candidate", {"size": len(candidate_text)})

    # -----------------------------------------------------------------
    # Stage 2.5 — atom-to-policy traceback.
    # -----------------------------------------------------------------

    def write_stage2_5_traceback(self, traceback: list[Any]) -> None:
        path = self.base / "stage2_5" / "traceback.json"
        path.write_text(json.dumps([to_dict(t) for t in traceback], indent=2))
        self._event("stage2_5.traceback", {"atom_count": len(traceback)})

    def write_stage2_5_final_decision(self, approved: bool, reason: str = "") -> None:
        path = self.base / "stage2_5" / "final_user_decision.json"
        path.write_text(json.dumps({"approved": approved, "reason": reason}, indent=2))
        self._event("stage2_5.final_decision", {"approved": approved})

    # -----------------------------------------------------------------
    # Post-session edits.
    # -----------------------------------------------------------------

    def append_post_session_edit(self, edit: dict[str, Any]) -> None:
        path = self.base / "post_session_edits.json"
        existing: list[dict[str, Any]] = []
        if path.exists():
            existing = json.loads(path.read_text())
        existing.append(edit)
        path.write_text(json.dumps(existing, indent=2))
        self._event("post_session.edit", {"edit_summary": edit.get("summary", "")})

    # -----------------------------------------------------------------
    # Transcript flush.
    # -----------------------------------------------------------------

    def _event(self, event_type: str, payload: dict[str, Any]) -> None:
        self._events.append(
            {
                "ts": datetime.datetime.utcnow().isoformat() + "Z",
                "event": event_type,
                **payload,
            },
        )

    def flush_transcript(self) -> None:
        """Write transcript.json. Call at session end (or periodically)."""
        path = self.base / "transcript.json"
        path.write_text(json.dumps(self._events, indent=2))
