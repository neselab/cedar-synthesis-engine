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
import re
import shutil
from dataclasses import dataclass, field, replace
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
    to_dict,
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
from autocedar.property_elicitor import compile_plan, compile_plan_for_consistency
from autocedar.property_critic import PropertyCritique, accept_property_atom
from autocedar.intent_graph import build_property_intent_graph
from autocedar.schema_atomizer import (
    apply_schema_atoms_to_text,
    cedar_validate_schema,
    compose_and_validate,
)

MAX_SCHEMA_GAP_REPAIRS = 6
DEFAULT_MAX_PROPERTY_PROPOSALS = 128


# ---------------------------------------------------------------------------
# Callback type aliases.
# ---------------------------------------------------------------------------

# Stage 1: propose schema atoms from prose. Returns an ordered list.
Stage1AtomT = EntityAtom | AttributeAtom | ActionAtom | TypeAliasAtom
SchemaProposer = Callable[[str], list[Stage1AtomT]]

# Stage 2: propose the next property atom from prose + schema + review history.
PropertyProposer = Callable[
    [str, str, list[PropertyAtom], list[AtomDecision]],
    Optional[PropertyAtom],
]

# Stage 2 repair: propose one replacement after the user rejects a property atom.
PropertyRepairer = Callable[[str, str, PropertyAtom, str, list[PropertyAtom]], Optional[PropertyAtom]]

# Stage 2 decomposition critic: accept, request repair, or reject a proposed atom
# before it reaches HITL review.
PropertyCritic = Callable[
    [str, str, PropertyAtom, list[PropertyAtom], list[AtomDecision]],
    PropertyCritique,
]

# Stage 1 repair: propose one replacement after the user rejects a schema atom.
SchemaAtomRepairer = Callable[[str, Stage1AtomT, str, list[Stage1AtomT]], Optional[Stage1AtomT]]

# Stage 1 schema text fix: repair a composed schema that cedar validate rejects.
SchemaFixer = Callable[[str, str, str], str]

# Per-atom user review.
AtomReviewer = Callable[[Any], Any]

# Stage 3 synthesis: given a scenario directory, produce candidate.cedar.
# Returns the candidate path. Real implementations wrap eval_harness.
Synthesizer = Callable[[Path], Path]


def _stub_schema_proposer(spec_text: str) -> list[Stage1AtomT]:
    """Test helper: return no Stage 1 atoms."""
    _ = spec_text
    return []


def _stub_property_proposer(
    spec_text: str,
    schema_path: str,
    prior_atoms: list[PropertyAtom],
    prior_decisions: list[AtomDecision],
) -> Optional[PropertyAtom]:
    """Test helper: return no next Stage 2 atom."""
    _ = spec_text, schema_path, prior_atoms, prior_decisions
    return None


def _stub_property_critic(
    spec_text: str,
    schema_path: str,
    atom: PropertyAtom,
    prior_atoms: list[PropertyAtom],
    prior_decisions: list[AtomDecision],
) -> PropertyCritique:
    """Default critic: no-op so tests/callers can opt in deliberately."""
    _ = spec_text, schema_path, atom, prior_atoms, prior_decisions
    return accept_property_atom()


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
    repair_schema_atom: SchemaAtomRepairer | None = None,
    fix_schema: SchemaFixer | None = None,
    propose_property_atom: PropertyProposer | None = None,
    critique_property_atom: PropertyCritic | None = None,
    repair_property_atom: PropertyRepairer | None = None,
    review_atom: AtomReviewer | None = None,
    synthesize: Synthesizer | None = None,
    score_candidate: Callable[[str], CriticScore] = (
        lambda c: score_candidate_default(c, llm=stub_llm_scorer)
    ),
    schema_path_override: Optional[str] = None,
    max_property_proposals: int = DEFAULT_MAX_PROPERTY_PROPOSALS,
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
    draft: SchemaDraft | None = None
    approved_schema_atoms: list[Stage1AtomT] = []
    approved_schema_names: set[str] = set()
    schema_gaps: list[dict[str, Any]] = []
    schema_gap_repairs: list[dict[str, Any]] = []
    schema_gap_repair_count = 0

    spec_text = spec_path.read_text()
    session.write_input_spec(spec_text, filename=spec_path.name)

    if review_atom is None:
        raise ValueError("author() requires a review_atom callback for HITL review")
    if propose_property_atom is None:
        raise ValueError("author() requires a propose_property_atom callback")
    if synthesize is None:
        raise ValueError("author() requires a Stage 3 synthesize callback")
    critique_property_atom = critique_property_atom or _stub_property_critic

    # ──── Stage 1: schema atomization ────
    if schema_path_override:
        schema_text = Path(schema_path_override).read_text()
        # Persist the chosen schema in the session so later stages have
        # a stable on-disk path to point at.
        schema_dest = session.base / "stage1" / "final_schema.cedarschema"
        schema_dest.write_text(schema_text)
        schema_path: Path = schema_dest
        schema_ok, schema_error = cedar_validate_schema(schema_dest)
        session.write_stage1_schema_validation([
            {
                "attempt_number": 1,
                "schema_text": schema_text,
                "validator_passed": schema_ok,
                "validator_error": "" if schema_ok else schema_error,
                "llm_was_called": False,
                "schema_override": True,
            },
        ])
        session.write_stage1_proposed_atoms([])
        session.write_stage1_attribution_decisions([])
        session.write_stage1_decisions([])
        if not schema_ok:
            session.write_stage1_final_schema(schema_text)
            session.flush_transcript()
            return AuthorResult(
                session_id=session_id,
                session_dir=session.base,
                candidate_path=Path(""),
                plan=VerificationPlanDraft(properties=[]),
                schema_text=schema_text,
                final_user_approved=False,
                notes=[f"Stage 1 schema validation failed: {schema_error}"],
            )
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
            if atom.name in approved_schema_names:
                decisions.append(_duplicate_decision(atom.name, "schema"))
                continue
            current_atom = atom
            rejection_history: list[dict[str, str]] = []
            repairs_attempted = 0
            while True:
                reviewed_atom, decision = _normalize_review_result(
                    current_atom,
                    review_atom(current_atom),
                )
                if (
                    decision.action == "reject"
                    and repair_schema_atom is not None
                    and repairs_attempted < 2
                ):
                    reason = decision.reason or "Rejected during HITL schema review"
                    replacement = repair_schema_atom(
                        spec_text,
                        reviewed_atom,
                        reason,
                        approved_schema_atoms,
                    )
                    rejection_history.append(
                        {
                            "atom_name": reviewed_atom.name,
                            "reason": reason,
                        },
                    )
                    repairs_attempted += 1
                    if replacement is not None:
                        current_atom = replacement
                        continue
                if rejection_history:
                    decision.edit_delta.setdefault("reject_history", rejection_history)
                    if decision.action == "approve":
                        decision.edit_delta["replaced_after_reject"] = True
                break
            decisions.append(decision)
            if decision.action != "approve":
                continue
            if reviewed_atom.name in approved_schema_names:
                decisions[-1] = _duplicate_decision(reviewed_atom.name, "schema")
                continue
            _route_into_schema_draft(reviewed_atom, draft)
            approved_schema_atoms.append(reviewed_atom)
            approved_schema_names.add(reviewed_atom.name)
        session.write_stage1_decisions(decisions)
        _notify_review_stage_complete(review_atom, "Schema atom review", decisions)
        schema_path = session.base / "stage1" / "final_schema.cedarschema"
        if draft.entities or draft.actions or draft.type_aliases:
            validation = compose_and_validate(
                draft,
                schema_path,
                llm=_SchemaFixAdapter(fix_schema) if fix_schema is not None else None,
                spec_text=spec_text,
            )
            schema_text = validation.schema_text
            session.write_stage1_schema_validation([
                {
                    "attempt_number": attempt.attempt_number,
                    "schema_text": attempt.schema_text,
                    "validator_passed": attempt.validator_passed,
                    "validator_error": attempt.validator_error,
                    "llm_was_called": attempt.llm_was_called,
                    "schema_override": False,
                }
                for attempt in validation.attempts
            ])
            if not validation.succeeded:
                session.write_stage1_final_schema(schema_text)
                session.flush_transcript()
                last_error = validation.attempts[-1].validator_error if validation.attempts else ""
                return AuthorResult(
                    session_id=session_id,
                    session_dir=session.base,
                    candidate_path=Path(""),
                    plan=VerificationPlanDraft(properties=[]),
                    schema_text=schema_text,
                    final_user_approved=False,
                    notes=[f"Stage 1 schema validation failed: {last_error}"],
                )
        else:
            schema_text = "// empty schema (stub)\n"
            schema_path.write_text(schema_text)
            session.write_stage1_schema_validation([
                {
                    "attempt_number": 1,
                    "schema_text": schema_text,
                    "validator_passed": False,
                    "validator_error": "no approved schema atoms",
                    "llm_was_called": False,
                    "schema_override": False,
                },
            ])
            session.write_stage1_final_schema(schema_text)
            session.flush_transcript()
            return AuthorResult(
                session_id=session_id,
                session_dir=session.base,
                candidate_path=Path(""),
                plan=VerificationPlanDraft(properties=[]),
                schema_text=schema_text,
                final_user_approved=False,
                notes=["Stage 1 schema validation failed: no approved schema atoms"],
            )
    session.write_stage1_final_schema(schema_text)
    _notify_schema_ready(review_atom, schema_text)

    # ──── Stage 2: property elicitation ────
    # Stage 2 is intentionally clocked by HITL review: ask for one property
    # atom, verify it, let the human approve/edit/reject it, then pass that
    # review history into the next proposal.
    prop_atoms: list[PropertyAtom] = []
    attributions2: list[AttributionDecision] = []
    decisions2: list[AtomDecision] = []
    critic_reviews: list[dict[str, Any]] = []
    plan = VerificationPlanDraft(properties=[])
    verification_logs: dict[str, list[str]] = {}
    approved_property_names: set[str] = set()
    _notify_review_stage(review_atom, "Property intent review", None)
    for _ in range(max_property_proposals):
        atom = propose_property_atom(
            spec_text,
            str(schema_path),
            plan.properties,
            decisions2,
        )
        if atom is None:
            break
        prop_atoms.append(atom)
        attributions2.append(
            AttributionDecision(atom_name=atom.name, span_text=atom.source_excerpt),
        )
        session.write_stage2_proposed_atoms(prop_atoms)
        session.write_stage2_attribution_decisions(attributions2)
        if atom.name in approved_property_names:
            decisions2.append(_duplicate_decision(atom.name, "property"))
            break
        current_atom = atom
        critic_repairs_attempted = 0
        while True:
            deterministic_critique = _semantic_boundary_critique(current_atom, schema_text)
            critique = deterministic_critique or critique_property_atom(
                spec_text,
                str(schema_path),
                current_atom,
                plan.properties,
                decisions2,
            )
            critic_reviews.append(
                {
                    "atom_name": current_atom.name,
                    "decision": critique.decision,
                    "reason": critique.reason,
                    "tags": list(critique.tags),
                },
            )
            session.write_stage2_critic_reviews(critic_reviews)
            if critique.accepted:
                break
            decisions2.append(
                AtomDecision(
                    atom_name=current_atom.name,
                    action="reject",
                    reason=f"Stage 2 decomposition critic {critique.decision}: {critique.reason}",
                    edit_delta={
                        "critic_decision": critique.decision,
                        "critic_tags": list(critique.tags),
                    },
                    symbolic_verified=getattr(current_atom, "symbolic_verified", False),
                ),
            )
            session.write_stage2_decisions(decisions2)
            critic_schema_gap = _schema_gap_from_decision(decisions2[-1], schema_text=schema_text)
            if critic_schema_gap is not None:
                schema_gaps.append(critic_schema_gap)
                session.write_stage1_5_schema_gaps(schema_gaps)
                if schema_gap_repair_count >= MAX_SCHEMA_GAP_REPAIRS:
                    session.write_stage2_critic_reviews(critic_reviews)
                    session.write_stage2_intent_graph(
                        build_property_intent_graph(plan.properties, critic_reviews),
                    )
                    session.write_stage2_symbolic_verification_logs(verification_logs)
                    session.write_stage2_adversarial_examples(
                        {
                            a.name: [_example_to_dict(e) for e in a.examples_adversarial]
                            for a in plan.properties
                        },
                    )
                    _notify_review_stage_complete(review_atom, "Property intent review", decisions2)
                    _notify_property_plan_ready(review_atom, plan.properties)
                    session.flush_transcript()
                    return AuthorResult(
                        session_id=session_id,
                        session_dir=session.base,
                        candidate_path=Path(""),
                        plan=plan,
                        schema_text=schema_text,
                        final_user_approved=False,
                        notes=[
                            "Stage 2 found more schema gaps than the repair budget "
                            f"({MAX_SCHEMA_GAP_REPAIRS}); stopped before synthesis.",
                        ],
                    )
                repaired = _repair_schema_gap_and_validate(
                    spec_text=spec_text,
                    schema_text=schema_text,
                    schema_path=schema_path,
                    gap=critic_schema_gap,
                    session=session,
                    review_atom=review_atom,
                    propose_schema_atoms=propose_schema_atoms,
                    fix_schema=fix_schema,
                    draft=draft,
                    approved_schema_atoms=approved_schema_atoms,
                    approved_schema_names=approved_schema_names,
                    repair_records=schema_gap_repairs,
                )
                if repaired is None:
                    session.write_stage2_critic_reviews(critic_reviews)
                    session.write_stage2_intent_graph(
                        build_property_intent_graph(plan.properties, critic_reviews),
                    )
                    session.write_stage2_symbolic_verification_logs(verification_logs)
                    session.write_stage2_adversarial_examples(
                        {
                            a.name: [_example_to_dict(e) for e in a.examples_adversarial]
                            for a in plan.properties
                        },
                    )
                    _notify_review_stage_complete(review_atom, "Property intent review", decisions2)
                    _notify_property_plan_ready(review_atom, plan.properties)
                    session.flush_transcript()
                    return AuthorResult(
                        session_id=session_id,
                        session_dir=session.base,
                        candidate_path=Path(""),
                        plan=plan,
                        schema_text=schema_text,
                        final_user_approved=False,
                        notes=[
                            "Stage 2 found a schema gap but could not produce an approved "
                            f"schema repair for `{critic_schema_gap['atom_name']}`: "
                            f"{critic_schema_gap['reason']}",
                        ],
                    )
                schema_text = repaired
                schema_gap_repair_count += 1
                _notify_schema_ready(review_atom, schema_text)
                current_atom = None
                break
            if (
                critique.wants_repair
                and repair_property_atom is not None
                and critic_repairs_attempted < 2
            ):
                replacement = repair_property_atom(
                    spec_text,
                    str(schema_path),
                    current_atom,
                    critique.reason,
                    plan.properties,
                )
                critic_repairs_attempted += 1
                if replacement is not None:
                    replacement = _align_repaired_property_atom(
                        rejected_atom=current_atom,
                        replacement=replacement,
                        reason=critique.reason,
                    )
                    prop_atoms.append(replacement)
                    attributions2.append(
                        AttributionDecision(
                            atom_name=replacement.name,
                            span_text=replacement.source_excerpt,
                        ),
                    )
                    session.write_stage2_proposed_atoms(prop_atoms)
                    session.write_stage2_attribution_decisions(attributions2)
                    current_atom = replacement
                    continue
            current_atom = None
            break
        if current_atom is None:
            continue
        rejection_history: list[dict[str, str]] = []
        repairs_attempted = 0
        prior_repairs_attempted: set[str] = set()
        while True:
            symbolic_verify_atom(current_atom, str(schema_path), prior_atoms=plan.properties)
            verification_logs[current_atom.name] = list(current_atom.symbolic_verification_log)
            reviewed_atom, decision = _normalize_review_result(
                current_atom,
                review_atom(current_atom),
            )
            if (
                decision.action == "reject"
                and repair_property_atom is not None
                and repairs_attempted < 2
            ):
                reason = decision.reason or "Rejected during HITL property review"
                prior_repaired = _repair_conflicting_prior_property(
                    spec_text=spec_text,
                    schema_path=schema_path,
                    current_atom=current_atom,
                    reason=reason,
                    plan=plan,
                    approved_property_names=approved_property_names,
                    prior_repairs_attempted=prior_repairs_attempted,
                    repair_property_atom=repair_property_atom,
                    review_atom=review_atom,
                    decisions=decisions2,
                    session=session,
                    verification_logs=verification_logs,
                )
                if prior_repaired:
                    rejection_history.append(
                        {
                            "atom_name": reviewed_atom.name,
                            "reason": reason,
                            "action": "repaired_conflicting_prior_property",
                        },
                    )
                    continue
                replacement = repair_property_atom(
                    spec_text,
                    str(schema_path),
                    reviewed_atom,
                    reason,
                    plan.properties,
                )
                if replacement is not None:
                    replacement = _align_repaired_property_atom(
                        rejected_atom=reviewed_atom,
                        replacement=replacement,
                        reason=reason,
                    )
                rejection_history.append(
                    {
                        "atom_name": reviewed_atom.name,
                        "reason": reason,
                    },
                )
                repairs_attempted += 1
                if replacement is not None:
                    current_atom = replacement
                    continue
            if (
                decision.action == "approve"
                and isinstance(reviewed_atom, PropertyAtom)
                and reviewed_atom is not current_atom
            ):
                symbolic_verify_atom(reviewed_atom, str(schema_path), prior_atoms=plan.properties)
                verification_logs[reviewed_atom.name] = list(
                    reviewed_atom.symbolic_verification_log,
                )
            if rejection_history:
                decision.edit_delta.setdefault("reject_history", rejection_history)
                if decision.action == "approve":
                    decision.edit_delta["replaced_after_reject"] = True
            break
        # Mirror the symbolic_verified flag onto the decision log so the
        # corpus captures both fields per §1.4.
        decision.symbolic_verified = getattr(reviewed_atom, "symbolic_verified", False)
        if decision.action == "approve":
            if reviewed_atom.name in approved_property_names:
                decisions2.append(_duplicate_decision(reviewed_atom.name, "property"))
                continue
            reviewed_atom.intent_acknowledged_by_user = True
            plan.properties.append(reviewed_atom)
            approved_property_names.add(reviewed_atom.name)
        decisions2.append(decision)
        session.write_stage2_decisions(decisions2)
        schema_gap = _schema_gap_from_decision(decision, schema_text=schema_text)
        if schema_gap is not None:
            schema_gaps.append(schema_gap)
            session.write_stage1_5_schema_gaps(schema_gaps)
            if schema_gap_repair_count >= MAX_SCHEMA_GAP_REPAIRS:
                session.write_stage2_critic_reviews(critic_reviews)
                session.write_stage2_intent_graph(
                    build_property_intent_graph(plan.properties, critic_reviews),
                )
                session.write_stage2_symbolic_verification_logs(verification_logs)
                session.write_stage2_adversarial_examples(
                    {
                        a.name: [_example_to_dict(e) for e in a.examples_adversarial]
                        for a in plan.properties
                    },
                )
                _notify_review_stage_complete(review_atom, "Property intent review", decisions2)
                _notify_property_plan_ready(review_atom, plan.properties)
                session.flush_transcript()
                return AuthorResult(
                    session_id=session_id,
                    session_dir=session.base,
                    candidate_path=Path(""),
                    plan=plan,
                    schema_text=schema_text,
                    final_user_approved=False,
                    notes=[
                        "Stage 2 found more schema gaps than the repair budget "
                        f"({MAX_SCHEMA_GAP_REPAIRS}); stopped before synthesis.",
                    ],
                )
            repaired = _repair_schema_gap_and_validate(
                spec_text=spec_text,
                schema_text=schema_text,
                schema_path=schema_path,
                gap=schema_gap,
                session=session,
                review_atom=review_atom,
                propose_schema_atoms=propose_schema_atoms,
                fix_schema=fix_schema,
                draft=draft,
                approved_schema_atoms=approved_schema_atoms,
                approved_schema_names=approved_schema_names,
                repair_records=schema_gap_repairs,
            )
            if repaired is None:
                session.write_stage2_critic_reviews(critic_reviews)
                session.write_stage2_intent_graph(
                    build_property_intent_graph(plan.properties, critic_reviews),
                )
                session.write_stage2_symbolic_verification_logs(verification_logs)
                session.write_stage2_adversarial_examples(
                    {
                        a.name: [_example_to_dict(e) for e in a.examples_adversarial]
                        for a in plan.properties
                    },
                )
                _notify_review_stage_complete(review_atom, "Property intent review", decisions2)
                _notify_property_plan_ready(review_atom, plan.properties)
                session.flush_transcript()
                return AuthorResult(
                    session_id=session_id,
                    session_dir=session.base,
                    candidate_path=Path(""),
                    plan=plan,
                    schema_text=schema_text,
                    final_user_approved=False,
                    notes=[
                        "Stage 2 found a schema gap but could not produce an approved "
                        f"schema repair for `{schema_gap['atom_name']}`: "
                        f"{schema_gap['reason']}",
                    ],
                )
            schema_text = repaired
            schema_gap_repair_count += 1
            _notify_schema_ready(review_atom, schema_text)
            continue
    else:
        decisions2.append(
            AtomDecision(
                atom_name="stage2_property_elicitation_limit",
                action="reject",
                reason=(
                    "Stopped after "
                    f"{max_property_proposals} property proposals without an explicit completion signal."
                ),
            ),
        )

    # ──── Stage 1.5: schema amendments forced by approved sugar atoms ────
    amendments = _detect_schema_amendments(plan.properties)
    session.write_stage1_5_amendments(amendments)
    # Current behavior records host-application obligations; it does not
    # rewrite the schema automatically.

    if not prop_atoms:
        session.write_stage2_proposed_atoms(prop_atoms)
        session.write_stage2_attribution_decisions(attributions2)
    session.write_stage2_critic_reviews(critic_reviews)
    session.write_stage2_decisions(decisions2)
    _notify_review_stage_complete(review_atom, "Property intent review", decisions2)
    _notify_property_plan_ready(review_atom, plan.properties)
    session.write_stage2_intent_graph(
        build_property_intent_graph(plan.properties, critic_reviews),
    )
    session.write_stage2_symbolic_verification_logs(verification_logs)
    session.write_stage2_adversarial_examples(
        {a.name: [_example_to_dict(e) for e in a.examples_adversarial] for a in plan.properties},
    )

    # ──── Stage 1.75: pre-synthesis unsat detection ────
    consistency_plan = compile_plan_for_consistency(plan)
    consistency = symbolic_consistency_check(consistency_plan, str(schema_path))
    session.write_stage1_75_unsat_core(
        unsat=consistency.unsat,
        core=consistency.core,
        detail=consistency.detail,
    )
    if consistency.tool_error:
        session.flush_transcript()
        return AuthorResult(
            session_id=session_id,
            session_dir=session.base,
            candidate_path=Path(""),
            plan=plan,
            schema_text=schema_text,
            final_user_approved=False,
            notes=[f"Stage 1.75 verifier setup failed: {consistency.detail}"],
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

_SCHEMA_GAP_TAGS = {"schema-gap", "schema_gap", "schema-repair", "schema_repair"}

_SEMANTIC_BOUNDARY_RULES: tuple[dict[str, Any], ...] = (
    {
        "label": "current-semester",
        "triggers": (
            "current semester",
            "current course offering",
            "current course offerings",
        ),
        "schema_tokens": ("iscurrent", "currentsemester", "current_semester", "current"),
        "reference_tokens": ("iscurrent", "currentsemester", "current_semester", "current"),
        "proxy_examples": ("open registration", "add/drop period", "not completed"),
    },
    {
        "label": "upcoming-semester",
        "triggers": (
            "upcoming semester",
            "upcoming course offering",
            "upcoming course offerings",
        ),
        "schema_tokens": ("isupcoming", "upcomingsemester", "upcoming_semester", "upcoming"),
        "reference_tokens": ("isupcoming", "upcomingsemester", "upcoming_semester", "upcoming"),
        "proxy_examples": ("not completed", "open registration", "not closed"),
    },
    {
        "label": "completed-semester",
        "triggers": (
            "previously completed semester",
            "completed semester",
            "previous semester",
            "previously completed",
        ),
        "schema_tokens": (
            "iscompleted",
            "ispreviouslycompleted",
            "completedsemester",
            "previoussemester",
            "completed",
        ),
        "reference_tokens": (
            "iscompleted",
            "ispreviouslycompleted",
            "completedsemester",
            "previoussemester",
            "completed",
        ),
        "proxy_examples": ("not current", "not upcoming"),
    },
    {
        "label": "add-drop-period",
        "triggers": (
            "add/drop",
            "add or drop",
            "add-drop",
            "beginning of the semester",
            "beginning of each semester",
            "beginning-of-semester",
        ),
        "schema_tokens": ("isadddropperiod", "adddrop", "add_drop", "registrationwindow"),
        "reference_tokens": ("isadddropperiod", "adddrop", "add_drop", "registrationwindow"),
        "proxy_examples": ("registration not closed", "open registration"),
    },
    {
        "label": "no-conflict",
        "triggers": ("no conflict", "if there is no conflict", "without conflict"),
        "schema_tokens": ("conflict", "hasscheduleconflict", "noconflict"),
        "reference_tokens": ("conflict", "hasscheduleconflict", "noconflict"),
        "proxy_examples": ("eligible", "assigned"),
    },
    {
        "label": "extra-security",
        "triggers": (
            "extra security",
            "sensitive information",
            "prevent unauthorized access",
        ),
        "schema_tokens": ("extrasecurity", "strongauth", "mfa", "authentication", "security"),
        "reference_tokens": ("extrasecurity", "strongauth", "mfa", "authentication", "security"),
        "proxy_examples": ("principal type", "resource type"),
    },
    {
        "label": "campus-lan",
        "triggers": (
            "campus lan",
            "personal computers attached to the campus lan",
        ),
        "schema_tokens": ("campuslan", "fromcampus", "iscampus", "network"),
        "reference_tokens": ("campuslan", "fromcampus", "iscampus", "network"),
        "proxy_examples": ("student role", "professor role"),
    },
)


def _semantic_boundary_critique(
    atom: PropertyAtom,
    schema_text: str,
) -> PropertyCritique | None:
    """Catch semantic-boundary proxying before HITL property review.

    Frontier models often try to keep going with whatever schema they have.
    That is useful in chat, but dangerous in policy synthesis: a correlated
    proxy such as "not completed" is not the same intent atom as "upcoming
    semester." This guard makes the invariant executable. If the atom's own
    source/summary names a distinct boundary and the schema lacks an explicit
    hook, Stage 2 must repair schema first. If the schema has the hook but the
    reference omits it, Stage 2 must repair the property before HITL.
    """
    source_text = _semantic_normalize(
        " ".join(
            [
                atom.source_excerpt,
                atom.plain_english_summary,
                atom.rationale,
            ],
        ),
    )
    schema_norm = _semantic_normalize(schema_text)
    reference_norm = _semantic_normalize(atom.reference_cedar)

    for rule in _SEMANTIC_BOUNDARY_RULES:
        if not _semantic_contains_any(source_text, rule["triggers"]):
            continue
        schema_has_boundary = _semantic_contains_any(schema_norm, rule["schema_tokens"])
        reference_has_boundary = _semantic_contains_any(reference_norm, rule["reference_tokens"])
        if not schema_has_boundary:
            proxies = ", ".join(rule["proxy_examples"])
            return PropertyCritique(
                decision="repair",
                reason=(
                    f"schema gap: source requires an explicit {rule['label']} "
                    "boundary, but the current schema has no explicit hook for "
                    f"that concept. Do not approximate it with proxies such as "
                    f"{proxies}; repair the schema first."
                ),
                tags=["schema-gap", "semantic-boundary", rule["label"]],
            )
        if not reference_has_boundary and atom.constraint_type != "liveness":
            return PropertyCritique(
                decision="repair",
                reason=(
                    f"property omits the explicit {rule['label']} boundary "
                    "even though the schema exposes it; repair the atom to use "
                    "that schema hook instead of relying on a proxy."
                ),
                tags=["semantic-boundary", rule["label"]],
            )
    return None


def _semantic_normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9/]+", "", text.lower())


def _semantic_contains_any(haystack: str, needles: tuple[str, ...]) -> bool:
    return any(_semantic_normalize(needle) in haystack for needle in needles)

_SCHEMA_GAP_PHRASES = (
    "schema gap",
    "schema cannot",
    "schema can't",
    "not schema-expressible",
    "not expressible in the schema",
    "not expressible with the schema",
    "schema has no",
    "schema lacks",
    "schema needs",
    "needs schema",
    "requires schema",
    "missing schema",
    "missing from schema",
    "add to schema",
    "add this to schema",
    "add this field to schema",
    "add a field",
    "field in schema",
    "missing current semester",
    "missing current-semester",
    "current_semester",
    "current-semester boundary",
    "current semester boundary",
    "completed/previous-semester",
    "missing completed semester",
    "missing previous semester",
    "beginning-of-semester",
    "registration period field",
    "registration window field",
)

_NON_SCHEMA_GAP_PHRASES = (
    "not a schema gap",
    "not schema gap",
    "not a schema-gap",
    "property repair, not a schema gap",
    "property repair rather than a schema gap",
    "schema-implied",
    "schema implied",
    "schema shape",
    "principal/resource typing",
    "principal typing",
    "resource typing",
    "type check",
    "type-check",
)


def _schema_gap_from_decision(
    decision: AtomDecision,
    *,
    schema_text: str | None = None,
) -> dict[str, Any] | None:
    """Return a durable schema-repair record for explicit schema-gap rejections.

    The HITL contract is semantic: if the reviewer says the current schema cannot
    express a requirement, continuing to Stage 3 would synthesize against a known
    incomplete intent surface. We only classify explicit schema expressivity
    failures here; ordinary unwanted atoms remain normal rejections.
    """
    if decision.action != "reject":
        return None

    reason = (decision.reason or "").strip()
    reason_lower = reason.lower()
    if any(phrase in reason_lower for phrase in _NON_SCHEMA_GAP_PHRASES):
        return None

    raw_tags = decision.edit_delta.get("critic_tags", [])
    tags = {
        str(tag).strip().lower()
        for tag in raw_tags
        if str(tag).strip()
    } if isinstance(raw_tags, list) else set()

    has_schema_gap_tag = bool(tags & _SCHEMA_GAP_TAGS)
    has_schema_gap_phrase = any(phrase in reason_lower for phrase in _SCHEMA_GAP_PHRASES)
    if not (has_schema_gap_tag or has_schema_gap_phrase):
        return None
    if schema_text is not None and _schema_already_exposes_reported_boundary(
        reason_lower,
        tags,
        schema_text,
    ):
        return None

    return {
        "atom_name": decision.atom_name,
        "stage": "stage2_property_review",
        "reason": reason,
        "critic_tags": sorted(tags),
        "required_action": "repair_schema_before_synthesis",
    }


def _schema_already_exposes_reported_boundary(
    reason_lower: str,
    tags: set[str],
    schema_text: str,
) -> bool:
    """Reject false-positive schema gaps when the schema has the named hook.

    The LLM critic can correctly spot a missing property condition but
    over-label it as a schema gap. If the schema already exposes the relevant
    field/process, the right move is property repair, not adding a duplicate
    schema relation.
    """
    reported = _semantic_normalize(" ".join([reason_lower, *sorted(tags)]))
    schema_norm = _semantic_normalize(schema_text)

    tagged_boundaries = {
        "current-semester": (("iscurrent",),),
        "upcoming-semester": (("isupcoming",),),
        "completed-semester": (("iscompleted",), ("ispreviouslycompleted",)),
        "add-drop-period": (("isadddropperiod",), ("adddrop",)),
        "registration-closed": (("registrationprocess", "isclosed"),),
        "extra-security": (("hasextrasecurity",), ("strongauth",), ("mfa",), ("security",)),
        "campus-lan": (("iscampuslan",), ("fromcampus",), ("network",)),
        "no-conflict": (("hasscheduleconflict",), ("conflict",)),
    }
    matching_boundary_tags = [tag for tag in tags if tag in tagged_boundaries]
    if matching_boundary_tags:
        return all(
            any(
                all(token in schema_norm for token in schema_tokens)
                for schema_tokens in tagged_boundaries[tag]
            )
            for tag in matching_boundary_tags
        )

    exposed_boundaries = (
        (("currentsemester", "current"), (("iscurrent",),)),
        (("upcomingsemester", "upcoming"), (("isupcoming",),)),
        (
            ("completedsemester", "completed", "previoussemester"),
            (("iscompleted",), ("ispreviouslycompleted",)),
        ),
        (
            ("adddropperiod", "adddrop", "beginningofsemester"),
            (("isadddropperiod",), ("adddrop",)),
        ),
        (
            ("registrationclosed", "registrationisclosed", "registrationclosure", "isclosed"),
            (("registrationprocess", "isclosed"),),
        ),
        (
            ("extrasecurity", "sensitiveinformation"),
            (("hasextrasecurity",), ("strongauth",), ("mfa",), ("security",)),
        ),
        (("campuslan", "campusnetwork"), (("iscampuslan",), ("fromcampus",), ("network",))),
        (("noconflict", "scheduleconflict", "conflict"), (("hasscheduleconflict",), ("conflict",))),
    )
    for reported_tokens, schema_alternatives in exposed_boundaries:
        if (
            any(token in reported for token in reported_tokens)
            and any(
                all(token in schema_norm for token in schema_tokens)
                for schema_tokens in schema_alternatives
            )
        ):
            return True
    return False


_PRIOR_REPAIR_PHRASES = (
    "prior",
    "previous",
    "earlier",
    "already approved",
    "approved floor",
    "approved ceiling",
    "floor too broad",
    "ceiling too broad",
    "too-broad floor",
    "too broad floor",
    "fix the floor",
    "repair the floor",
    "repair prior",
)


def _repair_conflicting_prior_property(
    *,
    spec_text: str,
    schema_path: Path,
    current_atom: PropertyAtom,
    reason: str,
    plan: VerificationPlanDraft,
    approved_property_names: set[str],
    prior_repairs_attempted: set[str],
    repair_property_atom: PropertyRepairer,
    review_atom: AtomReviewer,
    decisions: list[AtomDecision],
    session: Session,
    verification_logs: dict[str, list[str]],
) -> bool:
    """Repair an approved prior property when HITL identifies it as the issue.

    Sometimes a later atom is correct but exposes that an earlier approved atom
    was too broad. For example, a registration ceiling may include an add/drop
    boundary that the earlier registration floor accidentally omitted. In that
    case repairing the current ceiling would weaken intent; the right operation
    is to surface a replacement for the conflicting prior atom and re-check the
    current atom after approval.
    """
    reason_lower = reason.lower()
    if not any(phrase in reason_lower for phrase in _PRIOR_REPAIR_PHRASES):
        return False

    for prior_name in _conflicting_prior_atom_names(current_atom.symbolic_verification_log):
        if prior_name in prior_repairs_attempted:
            continue
        prior_index = next(
            (i for i, atom in enumerate(plan.properties) if atom.name == prior_name),
            None,
        )
        if prior_index is None:
            continue
        prior_repairs_attempted.add(prior_name)
        prior_atom = plan.properties[prior_index]
        other_atoms = [
            atom
            for i, atom in enumerate(plan.properties)
            if i != prior_index
        ]
        replacement = repair_property_atom(
            spec_text,
            str(schema_path),
            prior_atom,
            reason,
            other_atoms,
        )
        if replacement is None:
            continue
        replacement = _align_repaired_property_atom(
            rejected_atom=prior_atom,
            replacement=replacement,
            reason=reason,
        )
        symbolic_verify_atom(replacement, str(schema_path), prior_atoms=other_atoms)
        verification_logs[replacement.name] = list(replacement.symbolic_verification_log)
        reviewed_replacement, repair_decision = _normalize_review_result(
            replacement,
            review_atom(replacement),
        )
        repair_decision.edit_delta.setdefault(
            "repaired_prior_for_consistency_conflict",
            {
                "prior_atom": prior_atom.name,
                "current_atom": current_atom.name,
                "reason": reason,
            },
        )
        repair_decision.symbolic_verified = getattr(
            reviewed_replacement,
            "symbolic_verified",
            False,
        )
        decisions.append(repair_decision)
        session.write_stage2_decisions(decisions)
        if repair_decision.action != "approve" or not isinstance(reviewed_replacement, PropertyAtom):
            continue
        reviewed_replacement.intent_acknowledged_by_user = True
        plan.properties[prior_index] = reviewed_replacement
        approved_property_names.discard(prior_atom.name)
        approved_property_names.add(reviewed_replacement.name)
        return True
    return False


def _conflicting_prior_atom_names(logs: list[str]) -> list[str]:
    text = "\n".join(logs)
    names = re.findall(r"Consistency check failed against `([^`]+)`", text)
    return list(dict.fromkeys(names))


def _repair_schema_gap_and_validate(
    *,
    spec_text: str,
    schema_text: str,
    schema_path: Path,
    gap: dict[str, Any],
    session: Session,
    review_atom: AtomReviewer,
    propose_schema_atoms: SchemaProposer | None,
    fix_schema: SchemaFixer | None,
    draft: SchemaDraft | None,
    approved_schema_atoms: list[Stage1AtomT],
    approved_schema_names: set[str],
    repair_records: list[dict[str, Any]],
) -> str | None:
    """Repair a Stage 2 schema gap through the Stage 1 HITL atom path.

    A schema gap means the property reviewer found real policy intent that the
    current schema cannot express. The right response is not to continue with a
    weakened property; it is to ask for missing schema atoms, review those atoms,
    apply only approved repairs, validate the schema, and then let Stage 2 ask
    for the next property against the repaired schema.
    """
    if propose_schema_atoms is None:
        return None

    repair_spec = _schema_gap_repair_spec(spec_text, schema_text, gap)
    proposed_atoms = propose_schema_atoms(repair_spec)
    repair_record: dict[str, Any] = {
        "gap": gap,
        "proposed_atoms": [to_dict(atom) for atom in proposed_atoms],
        "decisions": [],
        "approved_atoms": [],
        "schema_validation": [],
    }
    repair_records.append(repair_record)
    session.write_stage1_5_schema_gap_repairs(repair_records)
    if not proposed_atoms:
        return None

    _notify_review_stage(review_atom, "Schema repair review", len(proposed_atoms))
    approved_repairs: list[Stage1AtomT] = []
    for atom in proposed_atoms:
        reviewed_atom, decision = _normalize_review_result(atom, review_atom(atom))
        repair_record["decisions"].append(to_dict(decision))
        if decision.action != "approve":
            session.write_stage1_5_schema_gap_repairs(repair_records)
            continue
        approved_repairs.append(reviewed_atom)
        approved_schema_atoms.append(reviewed_atom)
        approved_schema_names.add(reviewed_atom.name)
        repair_record["approved_atoms"].append(to_dict(reviewed_atom))
    _notify_review_stage_complete(
        review_atom,
        "Schema repair review",
        [AtomDecision(**d) for d in repair_record["decisions"]],
    )
    session.write_stage1_5_schema_gap_repairs(repair_records)

    if not approved_repairs:
        return None

    if draft is not None:
        for atom in approved_repairs:
            _route_into_schema_draft(atom, draft)
        validation = compose_and_validate(
            draft,
            schema_path,
            llm=_SchemaFixAdapter(fix_schema) if fix_schema is not None else None,
            spec_text=spec_text,
        )
        schema_text = validation.schema_text
        validation_log = [
            {
                "attempt_number": attempt.attempt_number,
                "schema_text": attempt.schema_text,
                "validator_passed": attempt.validator_passed,
                "validator_error": attempt.validator_error,
                "llm_was_called": attempt.llm_was_called,
                "schema_override": False,
                "schema_gap_repair": True,
            }
            for attempt in validation.attempts
        ]
        repair_record["schema_validation"] = validation_log
        session.write_stage1_schema_validation(validation_log)
        session.write_stage1_5_schema_gap_repairs(repair_records)
        if not validation.succeeded:
            return None
        session.write_stage1_final_schema(schema_text)
        return schema_text

    amended_schema = apply_schema_atoms_to_text(schema_text, approved_repairs)
    if amended_schema is None:
        repair_record["schema_validation"] = [
            {
                "attempt_number": 1,
                "schema_text": schema_text,
                "validator_passed": False,
                "validator_error": (
                    "approved schema repair atoms could not be applied "
                    "deterministically to the supplied schema"
                ),
                "llm_was_called": False,
                "schema_override": True,
                "schema_gap_repair": True,
            },
        ]
        session.write_stage1_5_schema_gap_repairs(repair_records)
        return None
    schema_path.write_text(amended_schema)
    schema_ok, schema_error = cedar_validate_schema(schema_path)
    validation_log = [
        {
            "attempt_number": 1,
            "schema_text": amended_schema,
            "validator_passed": schema_ok,
            "validator_error": "" if schema_ok else schema_error,
            "llm_was_called": False,
            "schema_override": True,
            "schema_gap_repair": True,
        },
    ]
    repair_record["schema_validation"] = validation_log
    session.write_stage1_schema_validation(validation_log)
    session.write_stage1_5_schema_gap_repairs(repair_records)
    if not schema_ok:
        return None
    session.write_stage1_final_schema(amended_schema)
    return amended_schema


def _schema_gap_repair_spec(
    spec_text: str,
    schema_text: str,
    gap: dict[str, Any],
) -> str:
    return (
        f"{spec_text}\n\n"
        "<schema_gap_repair>\n"
        "AutoCedar is in Stage 2 property review. The human rejected a "
        "property atom because the current schema cannot express a named "
        "requirement boundary.\n\n"
        f"Rejected property atom: {gap.get('atom_name', '')}\n"
        f"HITL reason: {gap.get('reason', '')}\n\n"
        "Current Cedar schema:\n"
        f"```cedarschema\n{schema_text}\n```\n\n"
        "Propose ONLY the missing Stage 1 schema atom(s) required to express "
        "this gap. Do not repeat the whole schema. If an existing entity needs "
        "a new field, emit an AttributeAtom for that entity. If an existing "
        "action needs new request context, emit an ActionAtom with the same "
        "action name and the additional context attribute(s). Keep the repair "
        "minimal and reviewable.\n\n"
        "If the rejected boundary is cross-cutting, repair the class of "
        "affected actions in one batch instead of only the rejected action. "
        "Examples: an active authenticated-session boundary should add the "
        "same `context.session`-style hook to all protected actions in the "
        "current schema whose authorization depends on a live requester; a "
        "patient-specific personal-representative or designated-provider "
        "boundary should add the same typed relationship hook to all actions "
        "that authorize represented-patient or designated-provider access. "
        "Still keep each emitted atom individually reviewable.\n"
        "</schema_gap_repair>\n"
    )


def _route_into_schema_draft(atom: Stage1AtomT, draft: SchemaDraft) -> None:
    """Insert an approved Stage 1 atom into the right SchemaDraft slot."""
    if isinstance(atom, EntityAtom):
        existing = draft.entities.get(atom.name)
        if existing is None:
            draft.entities[atom.name] = atom
        else:
            existing.members_of = list(dict.fromkeys(existing.members_of + atom.members_of))
            if atom.enum_values is not None:
                existing.enum_values = atom.enum_values
            existing.attributes.update(atom.attributes)
    elif isinstance(atom, ActionAtom):
        existing = draft.actions.get(atom.name)
        if existing is None:
            draft.actions[atom.name] = atom
        else:
            existing.principal_types = list(
                dict.fromkeys(existing.principal_types + atom.principal_types),
            )
            existing.resource_types = list(
                dict.fromkeys(existing.resource_types + atom.resource_types),
            )
            existing.context_attributes.update(atom.context_attributes)
            existing.parent_groups = list(
                dict.fromkeys(existing.parent_groups + atom.parent_groups),
            )
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


class _SchemaFixAdapter:
    """Adapter object matching ``compose_and_validate``'s LLM seam."""

    def __init__(self, fix_schema: SchemaFixer) -> None:
        self._fix_schema = fix_schema

    def fix_schema(
        self,
        *,
        schema_text: str,
        cedar_error_message: str,
        spec_text: str,
    ) -> str:
        return self._fix_schema(schema_text, cedar_error_message, spec_text)


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


def _duplicate_decision(atom_name: str, stage: str) -> AtomDecision:
    return AtomDecision(
        atom_name=atom_name,
        action="reject",
        reason=(
            f"Duplicate {stage} atom name already approved earlier; "
            "skipped to preserve one artifact per atom name."
        ),
        edit_delta={"duplicate_skipped": True},
    )


def _align_repaired_property_atom(
    *,
    rejected_atom: PropertyAtom,
    replacement: PropertyAtom,
    reason: str,
) -> PropertyAtom:
    """Preserve primitive proof direction unless the human asked to change it.

    A rejected floor with missing conditions still means "repair this required
    permission." If the model turns that into a ceiling, Stage 3 can lose the
    positive obligation. Preserve floor/ceiling direction by default; explicit
    user language like "should be a ceiling" or "wrong direction" can still
    request a real constraint-type change.
    """

    primitive_directions = {"floor", "ceiling"}
    if (
        rejected_atom.constraint_type not in primitive_directions
        or replacement.constraint_type not in primitive_directions
        or rejected_atom.constraint_type == replacement.constraint_type
        or _reason_requests_constraint_change(reason)
    ):
        return replacement
    return replace(
        replacement,
        constraint_type=rejected_atom.constraint_type,
        name=_rename_constraint_suffix(replacement.name, rejected_atom.constraint_type),
    )


def _reason_requests_constraint_change(reason: str) -> bool:
    normalized = reason.lower()
    phrases = (
        "should be a floor",
        "should be floor",
        "make it a floor",
        "use a floor",
        "not a ceiling",
        "should be a ceiling",
        "should be ceiling",
        "make it a ceiling",
        "use a ceiling",
        "not a floor",
        "wrong direction",
        "change direction",
        "instead",
    )
    return any(phrase in normalized for phrase in phrases)


def _rename_constraint_suffix(name: str, constraint_type: str) -> str:
    if constraint_type not in {"floor", "ceiling"}:
        return name
    other = "ceiling" if constraint_type == "floor" else "floor"
    if name.endswith(f"_{other}"):
        return name[: -(len(other) + 1)] + f"_{constraint_type}"
    return name


def _notify_review_stage(review_atom: AtomReviewer, label: str, total: int | None) -> None:
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
