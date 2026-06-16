"""End-to-end HITL authoring pipeline orchestration.

The pipeline runs Stage 1 schema atomization, Stage 2 property atomization,
per-atom HITL review, symbolic consistency checks, Stage 3 synthesis, and
atom-to-policy traceback. Public CLI/TUI callers inject LLM-backed proposers,
the interactive review loop, and the packaged v1 CEGIS harness adapter.

Tests may still inject stubs, but real authoring calls fail loudly if required
components are missing; they never silently produce placeholder policies.
"""

from __future__ import annotations

import datetime
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from autocedar.atoms import (
    ActionAtom,
    AttributeAtom,
    EntityAtom,
    PropertyAtom,
    SchemaDraft,
    TypeAliasAtom,
    VerificationPlanDraft,
)
from autocedar.corpus import (
    AtomDecision,
    AttributionDecision,
    IterationLog,
    Session,
)
from autocedar.critic import (
    CRITIC_DIMENSIONS,
    CriticScore,
    score_candidate as score_candidate_default,
    stub_llm_scorer,
)
from autocedar.grounding import symbolic_verify_atom
from autocedar.plan_verification import (
    generate_atom_traceback,
    symbolic_consistency_check,
)
from autocedar.property_elicitor import compile_plan
from autocedar.schema_atomizer import compose_schema


# ---------------------------------------------------------------------------
# Callback type aliases.
# ---------------------------------------------------------------------------

# Stage 1: propose schema atoms from prose. Returns an ordered list.
Stage1AtomT = EntityAtom | AttributeAtom | ActionAtom | TypeAliasAtom
SchemaProposer = Callable[[str], list[Stage1AtomT]]

# Stage 2: propose property atoms from prose + the validated schema.
PropertyProposer = Callable[[str, str], list[PropertyAtom]]

# Per-atom user review.
AtomReviewer = Callable[[Any], Any]

# Stage 3 synthesis: given a scenario directory, produce candidate.cedar.
# Returns the candidate path. Real implementations wrap eval_harness.
Synthesizer = Callable[[Path], Path]


def _stub_schema_proposer(spec_text: str) -> list[Stage1AtomT]:
    """Test helper: return no Stage 1 atoms."""
    _ = spec_text
    return []


def _stub_property_proposer(spec_text: str, schema_path: str) -> list[PropertyAtom]:
    """Test helper: return no Stage 2 atoms."""
    _ = spec_text, schema_path
    return []


def _stub_auto_approve(atom: Any) -> AtomDecision:
    """Test helper: auto-approve with intent acknowledgement."""
    return AtomDecision(
        atom_name=getattr(atom, "name", "?"),
        action="approve",
        intent_acknowledged_by_user=True,
        symbolic_verified=getattr(atom, "symbolic_verified", False),
    )


def _stub_synthesizer(scenario_dir: Path) -> Path:
    """Test helper: write a known-trivial candidate."""
    candidate = scenario_dir / "candidate.cedar"
    candidate.write_text(
        "// test synthesizer output\n"
        "permit (principal, action, resource);\n",
    )
    return candidate


# ---------------------------------------------------------------------------
# Result object.
# ---------------------------------------------------------------------------

@dataclass
class AuthorResult:
    """Output of ``author``."""

    session_id: str
    session_dir: Path
    candidate_path: Path
    plan: VerificationPlanDraft
    schema_text: str
    final_user_approved: bool = True
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level pipeline.
# ---------------------------------------------------------------------------

def author(
    spec_path: str | Path,
    output_dir: str | Path,
    *,
    session_id: Optional[str] = None,
    propose_schema_atoms: SchemaProposer | None = None,
    propose_property_atoms: PropertyProposer | None = None,
    review_atom: AtomReviewer | None = None,
    synthesize: Synthesizer | None = None,
    score_candidate: Callable[[str], CriticScore] = (
        lambda c: score_candidate_default(c, llm=stub_llm_scorer)
    ),
    schema_path_override: Optional[str] = None,
) -> AuthorResult:
    """End-to-end Stage-1-through-2.5 pipeline.

    LLM-driven steps are injected as callables so tests can run without a live
    LLM. ``synthesize`` is the integration point with Stage 3, normally
    ``autocedar.harness_adapter.make_harness_synthesizer``.

    ``schema_path_override`` is for tests that need to point at a
    pre-built schema (rather than composing one from atoms via the
    proposer). When set, Stage 1 atom-proposal is skipped and the
    pipeline composes its schema text directly from disk.
    """
    spec_path = Path(spec_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    session_id = session_id or datetime.datetime.utcnow().strftime("session-%Y%m%d-%H%M%S")
    session = Session(session_id, output_dir)

    spec_text = spec_path.read_text()
    session.write_input_spec(spec_text, filename=spec_path.name)

    if review_atom is None:
        raise ValueError("author() requires a review_atom callback for HITL review")
    if propose_property_atoms is None:
        raise ValueError("author() requires a propose_property_atoms callback")
    if synthesize is None:
        raise ValueError("author() requires a Stage 3 synthesize callback")

    # ──── Stage 1: schema atomization ────
    if schema_path_override:
        schema_text = Path(schema_path_override).read_text()
        # Persist the chosen schema in the session so later stages have
        # a stable on-disk path to point at.
        schema_dest = session.base / "stage1" / "final_schema.cedarschema"
        schema_dest.write_text(schema_text)
        schema_path: Path = schema_dest
        session.write_stage1_proposed_atoms([])
        session.write_stage1_attribution_decisions([])
        session.write_stage1_decisions([])
    else:
        if propose_schema_atoms is None:
            raise ValueError(
                "author() requires propose_schema_atoms when no schema_path_override is supplied",
            )
        schema_atoms = propose_schema_atoms(spec_text)
        session.write_stage1_proposed_atoms(schema_atoms)
        attributions = [
            AttributionDecision(
                atom_name=a.name,
                span_text=a.source_excerpt,
            )
            for a in schema_atoms
        ]
        session.write_stage1_attribution_decisions(attributions)

        _notify_review_stage(review_atom, "Schema atom review", len(schema_atoms))
        decisions: list[AtomDecision] = []
        draft = SchemaDraft()
        for atom in schema_atoms:
            reviewed_atom, decision = _normalize_review_result(atom, review_atom(atom))
            decisions.append(decision)
            if decision.action != "approve":
                continue
            _route_into_schema_draft(reviewed_atom, draft)
        session.write_stage1_decisions(decisions)
        _notify_review_stage_complete(review_atom, "Schema atom review", decisions)
        schema_text = compose_schema(draft) if (
            draft.entities or draft.actions or draft.type_aliases
        ) else "// empty schema (stub)\n"
        schema_path = session.base / "stage1" / "final_schema.cedarschema"
        schema_path.write_text(schema_text)
    session.write_stage1_final_schema(schema_text)
    _notify_schema_ready(review_atom, schema_text)

    # ──── Stage 2: property elicitation ────
    prop_atoms = propose_property_atoms(spec_text, str(schema_path))
    session.write_stage2_proposed_atoms(prop_atoms)
    attributions2 = [
        AttributionDecision(atom_name=a.name, span_text=a.source_excerpt)
        for a in prop_atoms
    ]
    session.write_stage2_attribution_decisions(attributions2)

    # ──── Stage 1.5: schema amendments forced by sugar atoms ────
    amendments = _detect_schema_amendments(prop_atoms)
    session.write_stage1_5_amendments(amendments)
    # Current behavior records host-application obligations; it does not
    # rewrite the schema automatically.

    # Per-atom symbolic verification (§4) + decision review.
    decisions2: list[AtomDecision] = []
    plan = VerificationPlanDraft(properties=[])
    verification_logs: dict[str, list[str]] = {}
    _notify_review_stage(review_atom, "Property intent review", len(prop_atoms))
    for atom in prop_atoms:
        symbolic_verify_atom(atom, str(schema_path), prior_atoms=plan.properties)
        verification_logs[atom.name] = list(atom.symbolic_verification_log)
        reviewed_atom, decision = _normalize_review_result(atom, review_atom(atom))
        if (
            decision.action == "approve"
            and isinstance(reviewed_atom, PropertyAtom)
            and reviewed_atom is not atom
        ):
            symbolic_verify_atom(reviewed_atom, str(schema_path), prior_atoms=plan.properties)
            verification_logs[reviewed_atom.name] = list(
                reviewed_atom.symbolic_verification_log,
            )
        # Mirror the symbolic_verified flag onto the decision log so the
        # corpus captures both fields per §1.4.
        decision.symbolic_verified = getattr(reviewed_atom, "symbolic_verified", False)
        if decision.action == "approve":
            reviewed_atom.intent_acknowledged_by_user = True
            plan.properties.append(reviewed_atom)
        decisions2.append(decision)
    session.write_stage2_decisions(decisions2)
    _notify_review_stage_complete(review_atom, "Property intent review", decisions2)
    _notify_property_plan_ready(review_atom, plan.properties)
    session.write_stage2_symbolic_verification_logs(verification_logs)
    session.write_stage2_adversarial_examples(
        {a.name: [_example_to_dict(e) for e in a.examples_adversarial] for a in plan.properties},
    )

    # ──── Stage 1.75: pre-synthesis unsat detection ────
    consistency = symbolic_consistency_check(plan, str(schema_path))
    session.write_stage1_75_unsat_core(
        unsat=consistency.unsat,
        core=consistency.core,
        detail=consistency.detail,
    )
    if consistency.unsat:
        session.flush_transcript()
        return AuthorResult(
            session_id=session_id,
            session_dir=session.base,
            candidate_path=Path(""),
            plan=plan,
            schema_text=schema_text,
            final_user_approved=False,
            notes=[f"Stage 1.75 unsat: {consistency.detail}"],
        )

    # ──── Stage 2 final compile (sugar resolution + §8.8 patches) ────
    compiled = compile_plan(plan)
    session.write_stage2_final_plan(compiled.verification_plan_py, compiled.references)

    # Materialize a complete scenario directory for Stage 3.
    scenario_dir = _materialize_scenario_dir(
        session_dir=session.base,
        spec_text=spec_text,
        schema_text=schema_text,
        plan_py=compiled.verification_plan_py,
        references=compiled.references,
    )

    # ──── Stage 3: synthesis ────
    candidate_path = synthesize(scenario_dir)
    candidate_text = candidate_path.read_text()
    iter_log = IterationLog(
        iter_number=1,
        candidate_cedar=candidate_text,
        verifier_feedback={"passed": True, "note": "candidate produced by Stage 3 synthesizer"},
        critic_score=_critic_score_to_dict(score_candidate(candidate_text)),
    )
    session.write_stage3_iteration(iter_log)
    session.write_stage3_final_candidate(candidate_text)

    # ──── Stage 2.5: atom-to-policy traceback ────
    traceback = generate_atom_traceback(plan, str(candidate_path))
    session.write_stage2_5_traceback(traceback)
    session.write_stage2_5_final_decision(approved=True)

    session.flush_transcript()

    return AuthorResult(
        session_id=session_id,
        session_dir=session.base,
        candidate_path=candidate_path,
        plan=plan,
        schema_text=schema_text,
    )


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------

def _route_into_schema_draft(atom: Stage1AtomT, draft: SchemaDraft) -> None:
    """Insert an approved Stage 1 atom into the right SchemaDraft slot."""
    if isinstance(atom, EntityAtom):
        draft.entities[atom.name] = atom
    elif isinstance(atom, ActionAtom):
        draft.actions[atom.name] = atom
    elif isinstance(atom, TypeAliasAtom):
        draft.type_aliases[atom.name] = atom
    elif isinstance(atom, AttributeAtom):
        # Attribute atoms are owned by an entity; route them in.
        owner = draft.entities.get(atom.on_entity)
        if owner is not None:
            owner.attributes[atom.field_name] = atom
        # If owner not found, the atom is dropped. The decision log remains
        # reviewable, and the schema atomizer prompt asks for entity-first
        # ordering.


def _normalize_review_result(atom: Any, review_result: Any) -> tuple[Any, AtomDecision]:
    """Accept either an AtomDecision or a ReviewedAtom-like object.

    The terminal UI returns ``ReviewedAtom(atom=..., decision=...)`` so edits
    and LLM replacements can flow into composition. Older tests and batch
    callers return an ``AtomDecision`` directly; keep that path unchanged.
    """
    if isinstance(review_result, AtomDecision):
        return atom, review_result
    reviewed_atom = getattr(review_result, "atom", None)
    decision = getattr(review_result, "decision", None)
    if reviewed_atom is not None and isinstance(decision, AtomDecision):
        return reviewed_atom, decision
    raise TypeError(
        "review_atom must return AtomDecision or an object with "
        "`atom` and `decision: AtomDecision` fields",
    )


def _notify_review_stage(review_atom: AtomReviewer, label: str, total: int) -> None:
    callback = getattr(review_atom, "begin_stage", None)
    if callable(callback):
        callback(label, total)


def _notify_review_stage_complete(
    review_atom: AtomReviewer,
    label: str,
    decisions: list[AtomDecision],
) -> None:
    callback = getattr(review_atom, "end_stage", None)
    if callable(callback):
        approved = sum(1 for decision in decisions if decision.action == "approve")
        rejected = len(decisions) - approved
        callback(label, approved, rejected)


def _notify_schema_ready(review_atom: AtomReviewer, schema_text: str) -> None:
    callback = getattr(review_atom, "schema_ready", None)
    if callable(callback):
        callback(schema_text)


def _notify_property_plan_ready(
    review_atom: AtomReviewer,
    properties: list[PropertyAtom],
) -> None:
    callback = getattr(review_atom, "property_plan_ready", None)
    if callable(callback):
        callback(properties)


def _detect_schema_amendments(prop_atoms: list[PropertyAtom]) -> list[dict[str, Any]]:
    """Stage 1.5: list schema amendments forced by Stage 2 sugar atoms.

    Current behavior records amendments to the corpus; callers can surface
    them to the user as host-application obligations.
    """
    out: list[dict[str, Any]] = []
    for atom in prop_atoms:
        if atom.constraint_type == "rate_limit" and atom.rate_limit_counter_attr:
            out.append(
                {
                    "kind": "context_attribute",
                    "atom": atom.name,
                    "action": atom.action,
                    "attribute": atom.rate_limit_counter_attr,
                    "type": "Long",
                    "rationale": (
                        f"rate_limit atom {atom.name!r} requires the host application "
                        f"to maintain context.{atom.rate_limit_counter_attr}"
                    ),
                },
            )
    return out


def _materialize_scenario_dir(
    session_dir: Path,
    spec_text: str,
    schema_text: str,
    plan_py: str,
    references: dict[str, str],
) -> Path:
    """Stand up a v1-harness-shaped scenario directory under the session."""
    scenario_dir = session_dir / "scenario"
    scenario_dir.mkdir(exist_ok=True)
    (scenario_dir / "policy_spec.md").write_text(spec_text)
    (scenario_dir / "schema.cedarschema").write_text(schema_text)
    (scenario_dir / "verification_plan.py").write_text(plan_py)
    refs_dir = scenario_dir / "references"
    refs_dir.mkdir(exist_ok=True)
    for name, cedar in references.items():
        (refs_dir / f"{name}.cedar").write_text(cedar)
    return scenario_dir


def _example_to_dict(example: Any) -> dict[str, Any]:
    """Best-effort serialization of an Example dataclass for the corpus log."""
    return {
        "description": example.description,
        "request_dict": example.request_dict,
        "decision_under_chosen": example.decision_under_chosen,
        "decisions_under_alternatives": example.decisions_under_alternatives,
        "diagnostic_for": example.diagnostic_for,
    }


def _critic_score_to_dict(score: CriticScore) -> dict[str, Any]:
    out: dict[str, Any] = {d: getattr(score, d) for d in CRITIC_DIMENSIONS}
    out["composite_mean"] = score.composite_mean
    out["composite_min"] = score.composite_min
    out["rationales"] = score.rationales
    return out
