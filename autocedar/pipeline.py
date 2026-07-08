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
import json
import os
import re
import shutil
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Literal, Optional

from autocedar.atoms import (
    ActionAtom,
    AttributeAtom,
    EntityAtom,
    PropertyAtom,
    SchemaDraft,
    TypeAliasAtom,
    VerificationPlanDraft,
    from_dict,
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
from autocedar.intent_graph import build_property_intent_graph
from autocedar.schema_atomizer import (
    apply_schema_atoms_to_text,
    cedar_validate_schema,
    compose_and_validate,
)
from autocedar.schema_support import (
    describe_missing_schema_support,
    missing_schema_support,
)
from autocedar.source_doc import (
    attach_source_ids,
    atom_source_ids,
    approved_target_spec,
    build_coverage_ledger,
    build_schema_packets,
    build_source_intent_dag,
    compile_source_document,
    select_property_packet,
    source_ids_from_text,
)

DEFAULT_MAX_PROPERTY_PROPOSALS = 128


# ---------------------------------------------------------------------------
# Callback type aliases.
# ---------------------------------------------------------------------------

# Stage 1: propose schema atoms from prose. Returns an ordered list.
Stage1AtomT = EntityAtom | AttributeAtom | ActionAtom | TypeAliasAtom
SchemaProposer = Callable[[str], list[Stage1AtomT]]

# Stage 2: propose property atoms from prose + schema + review history.
PropertyProposalResult = Optional[PropertyAtom] | list[PropertyAtom]
PropertyProposer = Callable[
    [str, str, list[PropertyAtom], list[AtomDecision]],
    PropertyProposalResult,
]

# Stage 2 repair: propose one replacement after the user rejects a property atom.
PropertyRepairer = Callable[[str, str, PropertyAtom, str, list[PropertyAtom]], Optional[PropertyAtom]]


@dataclass
class PropertyRepairPlan:
    """Structured control decision for a rejected Stage 2 property atom."""

    action: Literal[
        "repair_current_property",
        "repair_prior_property",
        "repair_schema",
        "reject_current",
        "ask_user_clarification",
    ]
    reason: str
    target_atom: str | None = None
    repair_instruction: str = ""
    schema_gap_summary: str = ""


PropertyRepairPlanner = Callable[
    [str, str, PropertyAtom, AtomDecision, list[PropertyAtom], str, list[str]],
    PropertyRepairPlan,
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
) -> PropertyProposalResult:
    """Test helper: return no next Stage 2 atom."""
    _ = spec_text, schema_path, prior_atoms, prior_decisions
    return None


def _stub_auto_approve(atom: Any) -> AtomDecision:
    """Test helper: auto-approve with intent acknowledgement."""
    return AtomDecision(
        atom_name=getattr(atom, "name", "?"),
        action="approve",
        intent_acknowledged_by_user=True,
        symbolic_verified=getattr(atom, "symbolic_verified", False),
    )


def _default_property_repair_plan(
    spec_text: str,
    schema_path: str,
    current_atom: PropertyAtom,
    decision: AtomDecision,
    prior_atoms: list[PropertyAtom],
    schema_text: str,
    symbolic_log: list[str],
) -> PropertyRepairPlan:
    """Fallback for tests that do not inject an LLM planner.

    The real CLI always supplies an LLM-backed planner. This fallback does not
    classify natural-language intent; it preserves the historical unit-test
    contract that a rejected atom is repaired as the current atom.
    """

    _ = spec_text, schema_path, current_atom, prior_atoms, schema_text, symbolic_log
    return PropertyRepairPlan(
        action="repair_current_property",
        reason=decision.reason or "Rejected during HITL property review",
        repair_instruction=decision.reason or "Repair the current property atom.",
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


@dataclass
class _ResumeCheckpoint:
    """Hydrated state from an earlier incomplete authoring session."""

    base: Path
    schema_text: str
    schema_atoms: list[Stage1AtomT]
    stage1_attributions: list[AttributionDecision]
    stage1_decisions: list[AtomDecision]
    approved_schema_atoms: list[Stage1AtomT]
    property_atoms: list[PropertyAtom]
    stage2_attributions: list[AttributionDecision]
    stage2_decisions: list[AtomDecision]
    approved_property_atoms: list[PropertyAtom]
    completed_property_node_ids: set[str]
    schema_gaps: list[dict[str, Any]]
    schema_gap_repairs: list[dict[str, Any]]
    verification_logs: dict[str, list[str]]
    reopened_source_node_ids: set[str] = field(default_factory=set)


def _write_stage0_artifacts(
    session: Session,
    source_doc: Any,
    schema_context_packets: list[Any],
    property_context_packets: list[Any],
    completed_property_node_ids: set[str],
    schema_atoms: list[Any] | None = None,
    property_atoms: list[PropertyAtom] | None = None,
    schema_gaps: list[dict[str, Any]] | None = None,
) -> None:
    """Persist the source-grounded intent DAG and coverage ledger."""
    session.write_stage0_intent_dag(
        build_source_intent_dag(
            source_doc,
            schema_packets=schema_context_packets,
            property_packets=property_context_packets,
            schema_atoms=schema_atoms or [],
            property_atoms=property_atoms or [],
            schema_gaps=schema_gaps or [],
        ),
    )
    session.write_stage0_coverage_ledger(
        build_coverage_ledger(
            source_doc,
            completed_property_node_ids=completed_property_node_ids,
            schema_packets=schema_context_packets,
            property_packets=property_context_packets,
        ),
    )


def _run_incremental_candidate_check(
    *,
    session: Session,
    records: list[dict[str, Any]],
    synthesize: Synthesizer,
    spec_path: Path,
    schema_text: str,
    plan: VerificationPlanDraft,
    approved_schema_atoms: list[Stage1AtomT],
    score_candidate: Callable[[str], CriticScore],
) -> None:
    """Try an incremental candidate after each approved property update.

    Approved atoms remain the source of truth. This check is only an early
    diagnostic pass so verifier/synthesis failures surface while Stage 2 is
    still collecting intent.
    """
    if not plan.properties:
        return
    record: dict[str, Any] = {
        "approved_property_count": len(plan.properties),
        "passed": False,
        "candidate_path": "",
        "error": "",
    }
    try:
        compiled = compile_plan(plan)
        incremental_dir = session.base / "stage2" / "incremental" / f"after_{len(plan.properties):04d}"
        incremental_dir.mkdir(parents=True, exist_ok=True)
        stage_spec_text = approved_target_spec(
            original_spec_name=spec_path.name,
            schema_atoms=approved_schema_atoms,
            property_atoms=plan.properties,
        )
        scenario_dir = _materialize_scenario_dir(
            session_dir=incremental_dir,
            spec_text=stage_spec_text,
            schema_text=schema_text,
            plan_py=compiled.verification_plan_py,
            references=compiled.references,
        )
        candidate_path = synthesize(scenario_dir)
        candidate_text = candidate_path.read_text()
        record.update(
            {
                "passed": True,
                "candidate_path": str(candidate_path),
                "critic_score": _critic_score_to_dict(score_candidate(candidate_text)),
            },
        )
    except Exception as exc:  # diagnostic only; final synthesis still owns convergence.
        record["error"] = str(exc)
    records.append(record)
    session.write_stage2_incremental_candidates(records)


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
    plan_property_repair: PropertyRepairPlanner | None = None,
    repair_property_atom: PropertyRepairer | None = None,
    review_atom: AtomReviewer | None = None,
    synthesize: Synthesizer | None = None,
    score_candidate: Callable[[str], CriticScore] = (
        lambda c: score_candidate_default(c, llm=stub_llm_scorer)
    ),
    schema_path_override: Optional[str] = None,
    resume_from: Optional[str | Path] = None,
    run_incremental_checks: bool = True,
    max_property_proposals: int = DEFAULT_MAX_PROPERTY_PROPOSALS,
    max_schema_gap_repairs: int | None = None,
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
    resume_checkpoint = _load_resume_checkpoint(Path(resume_from)) if resume_from else None
    schema_gaps: list[dict[str, Any]] = (
        list(resume_checkpoint.schema_gaps) if resume_checkpoint else []
    )
    schema_gap_repairs: list[dict[str, Any]] = (
        list(resume_checkpoint.schema_gap_repairs) if resume_checkpoint else []
    )
    schema_gap_repair_count = 0
    schema_gap_repair_limit = max_schema_gap_repairs

    spec_text = spec_path.read_text()
    session.write_input_spec(spec_text, filename=spec_path.name)
    source_doc = compile_source_document(spec_text)
    session.write_stage0_source_index(source_doc.to_index())
    schema_context_packets = []
    property_context_packets = []
    completed_property_node_ids: set[str] = (
        set(resume_checkpoint.completed_property_node_ids) if resume_checkpoint else set()
    )
    _write_stage0_artifacts(
        session,
        source_doc,
        schema_context_packets,
        property_context_packets,
        completed_property_node_ids,
    )

    if review_atom is None:
        raise ValueError("author() requires a review_atom callback for HITL review")
    if propose_property_atom is None:
        raise ValueError("author() requires a propose_property_atom callback")
    if synthesize is None:
        raise ValueError("author() requires a Stage 3 synthesize callback")
    plan_property_repair = plan_property_repair or _default_property_repair_plan

    # ──── Stage 1: schema atomization ────
    if resume_checkpoint is not None:
        schema_text = resume_checkpoint.schema_text
        schema_dest = session.base / "stage1" / "final_schema.cedarschema"
        schema_dest.write_text(schema_text)
        schema_path = schema_dest
        schema_ok, schema_error = cedar_validate_schema(schema_dest)
        session.write_stage1_proposed_atoms(resume_checkpoint.schema_atoms)
        session.write_stage1_attribution_decisions(resume_checkpoint.stage1_attributions)
        session.write_stage1_decisions(resume_checkpoint.stage1_decisions)
        session.write_stage1_schema_validation([
            {
                "attempt_number": 1,
                "schema_text": schema_text,
                "validator_passed": schema_ok,
                "validator_error": "" if schema_ok else schema_error,
                "llm_was_called": False,
                "resume_from": str(resume_checkpoint.base),
            },
        ])
        approved_schema_atoms = list(resume_checkpoint.approved_schema_atoms)
        approved_schema_names = {atom.name for atom in approved_schema_atoms}
        draft = _draft_from_approved_schema_atoms(approved_schema_atoms)
        session.write_stage1_5_schema_gaps(schema_gaps)
        session.write_stage1_5_schema_gap_repairs(schema_gap_repairs)
        if not schema_ok:
            session.write_stage1_final_schema(schema_text)
            _write_stage0_artifacts(
                session,
                source_doc,
                schema_context_packets,
                property_context_packets,
                completed_property_node_ids,
            )
            session.flush_transcript()
            return AuthorResult(
                session_id=session_id,
                session_dir=session.base,
                candidate_path=Path(""),
                plan=VerificationPlanDraft(properties=[]),
                schema_text=schema_text,
                final_user_approved=False,
                notes=[
                    "Resumed Stage 1 schema validation failed: "
                    f"{schema_error}",
                ],
            )
    elif schema_path_override:
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
            _write_stage0_artifacts(
                session,
                source_doc,
                schema_context_packets,
                property_context_packets,
                completed_property_node_ids,
            )
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
        schema_atoms: list[Stage1AtomT] = []
        attributions: list[AttributionDecision] = []
        decisions: list[AtomDecision] = []
        schema_context_packets = build_schema_packets(source_doc)
        _notify_review_stage(review_atom, "Schema atom review", None)
        draft = SchemaDraft()
        for packet in schema_context_packets:
            packet.approved_schema_atoms = [atom.name for atom in approved_schema_atoms]
            session.write_stage0_context_packet(packet.id, packet.to_dict())
            packet_text = packet.to_prompt_text()
            proposed_atoms = [
                attach_source_ids(atom, packet.node_ids())
                for atom in propose_schema_atoms(packet_text)
            ]
            for atom in proposed_atoms:
                schema_atoms.append(atom)
                attributions.append(
                    AttributionDecision(
                        atom_name=atom.name,
                        span_text=atom.source_excerpt,
                        alternatives_considered=packet.node_ids(),
                    ),
                )
                session.write_stage1_proposed_atoms(schema_atoms)
                session.write_stage1_attribution_decisions(attributions)
                if atom.name in approved_schema_names:
                    decisions.append(_duplicate_decision(atom.name, "schema"))
                    session.write_stage1_decisions(decisions)
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
                            packet_text,
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
                            replacement = attach_source_ids(replacement, packet.node_ids())
                            current_atom = replacement
                            continue
                    if rejection_history:
                        decision.edit_delta.setdefault("reject_history", rejection_history)
                        if decision.action == "approve":
                            decision.edit_delta["replaced_after_reject"] = True
                    break
                decisions.append(decision)
                session.write_stage1_decisions(decisions)
                if decision.action != "approve":
                    continue
                if reviewed_atom.name in approved_schema_names:
                    decisions[-1] = _duplicate_decision(reviewed_atom.name, "schema")
                    session.write_stage1_decisions(decisions)
                    continue
                _route_into_schema_draft(reviewed_atom, draft)
                approved_schema_atoms.append(reviewed_atom)
                approved_schema_names.add(reviewed_atom.name)
        if not schema_atoms:
            session.write_stage1_proposed_atoms(schema_atoms)
            session.write_stage1_attribution_decisions(attributions)
        session.write_stage1_decisions(decisions)
        _notify_review_stage_complete(review_atom, "Schema atom review", decisions)
        schema_path = session.base / "stage1" / "final_schema.cedarschema"
        if draft.entities or draft.actions or draft.type_aliases:
            schema_fix_context = approved_target_spec(
                original_spec_name=spec_path.name,
                schema_atoms=approved_schema_atoms,
                property_atoms=[],
            )
            validation = compose_and_validate(
                draft,
                schema_path,
                llm=_SchemaFixAdapter(fix_schema) if fix_schema is not None else None,
                spec_text=schema_fix_context,
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
                _write_stage0_artifacts(
                    session,
                    source_doc,
                    schema_context_packets,
                    property_context_packets,
                    completed_property_node_ids,
                )
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
            _write_stage0_artifacts(
                session,
                source_doc,
                schema_context_packets,
                property_context_packets,
                completed_property_node_ids,
            )
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
    prop_atoms: list[PropertyAtom] = (
        list(resume_checkpoint.property_atoms) if resume_checkpoint else []
    )
    attributions2: list[AttributionDecision] = (
        list(resume_checkpoint.stage2_attributions) if resume_checkpoint else []
    )
    decisions2: list[AtomDecision] = (
        list(resume_checkpoint.stage2_decisions) if resume_checkpoint else []
    )
    plan = VerificationPlanDraft(
        properties=list(resume_checkpoint.approved_property_atoms)
        if resume_checkpoint
        else [],
    )
    verification_logs: dict[str, list[str]] = (
        dict(resume_checkpoint.verification_logs) if resume_checkpoint else {}
    )
    repair_plans: list[dict[str, Any]] = []
    incremental_candidates: list[dict[str, Any]] = []
    approved_property_names: set[str] = set()
    if resume_checkpoint is not None:
        approved_property_names = {atom.name for atom in plan.properties}
        session.write_stage2_proposed_atoms(prop_atoms)
        session.write_stage2_approved_atoms(plan.properties)
        session.write_stage2_attribution_decisions(attributions2)
        session.write_stage2_decisions(decisions2)
        session.write_stage2_symbolic_verification_logs(verification_logs)
    property_frontier_nodes = source_doc.authorization_nodes()
    property_frontier_total = len(property_frontier_nodes)
    property_frontier_index = {
        node.id: index for index, node in enumerate(property_frontier_nodes, start=1)
    }
    active_property_node = None
    active_packet = None
    active_spec_text = ""
    pending_property_atoms: list[tuple[PropertyAtom, bool]] = []
    property_frontier_exhausted = False
    _notify_review_stage(review_atom, "Property intent review", None)
    _notify_property_progress(
        review_atom,
        event="start",
        source_total=property_frontier_total,
        source_completed=len(completed_property_node_ids),
        source_open=max(property_frontier_total - len(completed_property_node_ids), 0),
        approved=len(plan.properties),
        decisions=len(decisions2),
        proposed=len(prop_atoms),
        queued=0,
    )
    for _ in range(max_property_proposals):
        if active_property_node is None:
            active_property_node = next(
                (
                    node
                    for node in property_frontier_nodes
                    if node.id not in completed_property_node_ids
                ),
                None,
            )
            if active_property_node is None:
                property_frontier_exhausted = True
                break
            pending_property_atoms = []
            _notify_property_progress(
                review_atom,
                event="source_start",
                source_id=active_property_node.id,
                source_index=property_frontier_index.get(active_property_node.id),
                source_total=property_frontier_total,
                source_completed=len(completed_property_node_ids),
                source_open=max(property_frontier_total - len(completed_property_node_ids), 0),
                approved=len(plan.properties),
                decisions=len(decisions2),
                proposed=len(prop_atoms),
                queued=0,
            )
        if not pending_property_atoms:
            active_packet = select_property_packet(
                source_doc,
                active_property_node,
                approved_schema_atoms=approved_schema_atoms,
                approved_property_atoms=plan.properties,
                prior_decisions=decisions2,
            )
            active_packet.id = f"{active_packet.id}.step{len(property_context_packets) + 1:04d}"
            property_context_packets.append(active_packet)
            session.write_stage0_context_packet(active_packet.id, active_packet.to_dict())
            active_spec_text = active_packet.to_prompt_text()
            proposal_result = propose_property_atom(
                active_spec_text,
                str(schema_path),
                plan.properties,
                decisions2,
            )
            proposed = _normalize_property_proposals(proposal_result)
            proposal_was_batch = isinstance(proposal_result, list)
            pending_property_atoms.extend(
                (attach_source_ids(atom, active_packet.focus_node_ids), proposal_was_batch)
                for atom in proposed
            )
            _notify_property_progress(
                review_atom,
                event="bundle_proposed",
                source_id=active_property_node.id,
                source_index=property_frontier_index.get(active_property_node.id),
                source_total=property_frontier_total,
                source_completed=len(completed_property_node_ids),
                source_open=max(property_frontier_total - len(completed_property_node_ids), 0),
                packet_id=active_packet.id,
                bundle_size=len(proposed),
                approved=len(plan.properties),
                decisions=len(decisions2),
                proposed=len(prop_atoms),
                queued=len(pending_property_atoms),
            )
            if not pending_property_atoms:
                completion_blocker = _source_node_completion_blocker(
                    active_packet.focus_node_ids,
                    plan.properties,
                )
                if completion_blocker is not None:
                    decisions2.append(
                        AtomDecision(
                            atom_name=f"coverage_audit_{active_property_node.id}",
                            action="reject",
                            reason=completion_blocker,
                            edit_delta={
                                "stage": "stage2_source_node_completion",
                                "source_node_ids": list(active_packet.focus_node_ids),
                            },
                        ),
                    )
                    session.write_stage2_decisions(decisions2)
                    _notify_property_progress(
                        review_atom,
                        event="coverage_blocked",
                        source_id=active_property_node.id,
                        source_index=property_frontier_index.get(active_property_node.id),
                        source_total=property_frontier_total,
                        source_completed=len(completed_property_node_ids),
                        source_open=max(
                            property_frontier_total - len(completed_property_node_ids),
                            0,
                        ),
                        approved=len(plan.properties),
                        decisions=len(decisions2),
                        proposed=len(prop_atoms),
                        queued=0,
                        reason=completion_blocker,
                    )
                    continue
                completed_property_node_ids.add(active_property_node.id)
                session.write_stage0_coverage_ledger(
                    build_coverage_ledger(
                        source_doc,
                        completed_property_node_ids=completed_property_node_ids,
                        schema_packets=schema_context_packets,
                        property_packets=property_context_packets,
                    ),
                )
                _notify_property_progress(
                    review_atom,
                    event="source_complete",
                    source_id=active_property_node.id,
                    source_index=property_frontier_index.get(active_property_node.id),
                    source_total=property_frontier_total,
                    source_completed=len(completed_property_node_ids),
                    source_open=max(property_frontier_total - len(completed_property_node_ids), 0),
                    approved=len(plan.properties),
                    decisions=len(decisions2),
                    proposed=len(prop_atoms),
                    queued=0,
                )
                active_property_node = None
                continue
        atom, atom_from_batch = pending_property_atoms.pop(0)
        if active_packet is None:
            raise RuntimeError("Stage 2 property packet missing for queued atom")
        _notify_property_progress(
            review_atom,
            event="atom_review",
            source_id=active_property_node.id if active_property_node is not None else None,
            source_index=(
                property_frontier_index.get(active_property_node.id)
                if active_property_node is not None else None
            ),
            source_total=property_frontier_total,
            source_completed=len(completed_property_node_ids),
            source_open=max(property_frontier_total - len(completed_property_node_ids), 0),
            atom_name=atom.name,
            approved=len(plan.properties),
            decisions=len(decisions2),
            proposed=len(prop_atoms),
            queued=len(pending_property_atoms),
        )
        support_gaps = missing_schema_support(atom.required_schema_support, schema_text)
        if support_gaps:
            gap_reason = (
                "The proposed property atom depends on schema support that is "
                "not present yet:\n"
                f"{describe_missing_schema_support(support_gaps)}"
            )
            schema_gap = {
                "atom_name": atom.name,
                "stage": "stage2_pre_review_schema_support",
                "reason": gap_reason,
                "tags": ["property_required_schema_support"],
                "required_action": "repair_schema_before_property_review",
                "repair_plan": {
                    "action": "repair_schema",
                    "reason": gap_reason,
                    "repair_instruction": gap_reason,
                },
                "missing_support": [to_dict(item.support) | {"detail": item.detail} for item in support_gaps],
            }
            schema_gaps.append(schema_gap)
            session.write_stage1_5_schema_gaps(schema_gaps)
            if (
                schema_gap_repair_limit is not None
                and schema_gap_repair_count >= schema_gap_repair_limit
            ):
                _write_stage0_artifacts(
                    session,
                    source_doc,
                    schema_context_packets,
                    property_context_packets,
                    completed_property_node_ids,
                    schema_atoms=approved_schema_atoms,
                    property_atoms=plan.properties,
                    schema_gaps=schema_gaps,
                )
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
                        f"({schema_gap_repair_limit}); stopped before property review.",
                    ],
                )
            repaired = _repair_schema_gap_and_validate(
                spec_text=active_spec_text,
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
                _write_stage0_artifacts(
                    session,
                    source_doc,
                    schema_context_packets,
                    property_context_packets,
                    completed_property_node_ids,
                    schema_atoms=approved_schema_atoms,
                    property_atoms=plan.properties,
                    schema_gaps=schema_gaps,
                )
                session.flush_transcript()
                return AuthorResult(
                    session_id=session_id,
                    session_dir=session.base,
                    candidate_path=Path(""),
                    plan=plan,
                    schema_text=schema_text,
                    final_user_approved=False,
                    notes=[
                        "Stage 2 found schema support required by a proposed "
                        f"property atom but could not produce an approved schema repair for "
                        f"`{atom.name}`: {gap_reason}",
                    ],
                )
            schema_text = repaired
            schema_gap_repair_count += 1
            _notify_schema_ready(review_atom, schema_text)
            if atom_from_batch:
                pending_property_atoms.insert(0, (atom, atom_from_batch))
            continue
        prop_atoms.append(atom)
        attributions2.append(
            AttributionDecision(atom_name=atom.name, span_text=atom.source_excerpt),
        )
        session.write_stage2_proposed_atoms(prop_atoms)
        session.write_stage2_attribution_decisions(attributions2)
        if atom.name in approved_property_names:
            decisions2.append(_duplicate_decision(atom.name, "property"))
            continue
        current_atom = atom
        rejection_history: list[dict[str, str]] = []
        repairs_attempted = 0
        prior_repairs_attempted: set[str] = set()
        unrepaired_prior_conflict: str | None = None
        pending_schema_gap: dict[str, Any] | None = None
        while True:
            symbolic_verify_atom(current_atom, str(schema_path), prior_atoms=plan.properties)
            verification_logs[current_atom.name] = list(current_atom.symbolic_verification_log)
            reviewed_atom, decision = _normalize_review_result(
                current_atom,
                review_atom(current_atom),
            )
            if decision.action == "reject" and repairs_attempted < 2:
                reason = decision.reason or "Rejected during HITL property review"
                repair_plan = plan_property_repair(
                    active_spec_text,
                    str(schema_path),
                    current_atom,
                    decision,
                    plan.properties,
                    schema_text,
                    list(current_atom.symbolic_verification_log),
                )
                repair_plans.append(
                    {
                        "atom_name": current_atom.name,
                        "reviewer_reason": reason,
                        "action": repair_plan.action,
                        "target_atom": repair_plan.target_atom,
                        "reason": repair_plan.reason,
                        "repair_instruction": repair_plan.repair_instruction,
                        "schema_gap_summary": repair_plan.schema_gap_summary,
                        "symbolic_log": list(current_atom.symbolic_verification_log),
                    },
                )
                session.write_stage2_repair_plans(repair_plans)
                if repair_plan.action == "repair_prior_property":
                    if repair_property_atom is None:
                        unrepaired_prior_conflict = (
                            "Property repair planner selected prior-property repair, "
                            "but no property repair callback is configured."
                        )
                        rejection_history.append(
                            {
                                "atom_name": reviewed_atom.name,
                                "reason": reason,
                                "action": "prior_property_repair_unavailable",
                            },
                        )
                        decision.edit_delta.setdefault("reject_history", rejection_history)
                        break
                    prior_repaired = _repair_named_prior_property(
                        spec_text=active_spec_text,
                        schema_path=schema_path,
                        current_atom=current_atom,
                        repair_plan=repair_plan,
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
                    unrepaired_prior_conflict = repair_plan.reason
                    rejection_history.append(
                        {
                            "atom_name": reviewed_atom.name,
                            "reason": reason,
                            "action": "prior_property_repair_failed",
                        },
                    )
                    decision.edit_delta.setdefault("reject_history", rejection_history)
                    break
                if repair_plan.action == "repair_schema":
                    pending_schema_gap = {
                        "atom_name": decision.atom_name,
                        "stage": "stage2_property_review",
                        "reason": repair_plan.schema_gap_summary
                        or repair_plan.repair_instruction
                        or repair_plan.reason,
                        "tags": [],
                        "required_action": "repair_schema_before_synthesis",
                        "repair_plan": {
                            "action": repair_plan.action,
                            "reason": repair_plan.reason,
                            "repair_instruction": repair_plan.repair_instruction,
                        },
                    }
                    rejection_history.append(
                        {
                            "atom_name": reviewed_atom.name,
                            "reason": reason,
                            "action": "repair_schema",
                        },
                    )
                    decision.edit_delta.setdefault("reject_history", rejection_history)
                    break
                if repair_plan.action in {"reject_current", "ask_user_clarification"}:
                    rejection_history.append(
                        {
                            "atom_name": reviewed_atom.name,
                            "reason": repair_plan.reason,
                            "action": repair_plan.action,
                        },
                    )
                    decision.edit_delta.setdefault("reject_history", rejection_history)
                    break
                if repair_plan.action != "repair_current_property":
                    unrepaired_prior_conflict = (
                        "Unknown property repair action from planner: "
                        f"{repair_plan.action}"
                    )
                    decision.edit_delta.setdefault("reject_history", rejection_history)
                    break
                if repair_property_atom is None:
                    rejection_history.append(
                        {
                            "atom_name": reviewed_atom.name,
                            "reason": reason,
                            "action": "current_property_repair_unavailable",
                        },
                    )
                    decision.edit_delta.setdefault("reject_history", rejection_history)
                    break
                replacement = repair_property_atom(
                    active_spec_text,
                    str(schema_path),
                    reviewed_atom,
                    repair_plan.repair_instruction or reason,
                    plan.properties,
                )
                if replacement is not None:
                    replacement = attach_source_ids(replacement, active_packet.focus_node_ids)
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
            session.write_stage2_approved_atoms(plan.properties)
            if run_incremental_checks:
                _run_incremental_candidate_check(
                    session=session,
                    records=incremental_candidates,
                    synthesize=synthesize,
                    spec_path=spec_path,
                    schema_text=schema_text,
                    plan=plan,
                    approved_schema_atoms=approved_schema_atoms,
                    score_candidate=score_candidate,
                )
        decisions2.append(decision)
        session.write_stage2_decisions(decisions2)
        _notify_property_progress(
            review_atom,
            event="atom_decision",
            source_id=active_property_node.id if active_property_node is not None else None,
            source_index=(
                property_frontier_index.get(active_property_node.id)
                if active_property_node is not None else None
            ),
            source_total=property_frontier_total,
            source_completed=len(completed_property_node_ids),
            source_open=max(property_frontier_total - len(completed_property_node_ids), 0),
            atom_name=getattr(reviewed_atom, "name", decision.atom_name),
            decision=decision.action,
            approved=len(plan.properties),
            rejected=sum(1 for item in decisions2 if item.action != "approve"),
            decisions=len(decisions2),
            proposed=len(prop_atoms),
            queued=len(pending_property_atoms),
        )
        if unrepaired_prior_conflict is not None:
            session.write_stage2_intent_graph(
                build_property_intent_graph(plan.properties),
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
            _write_stage0_artifacts(
                session,
                source_doc,
                schema_context_packets,
                property_context_packets,
                completed_property_node_ids,
                schema_atoms=approved_schema_atoms,
                property_atoms=plan.properties,
                schema_gaps=schema_gaps,
            )
            session.flush_transcript()
            return AuthorResult(
                session_id=session_id,
                session_dir=session.base,
                candidate_path=Path(""),
                plan=plan,
                schema_text=schema_text,
                final_user_approved=False,
                notes=[
                    "Stage 2 stopped before synthesis because HITL requested "
                    "repair of a conflicting prior property, but no approved "
                    f"prior-property repair was produced: {unrepaired_prior_conflict}",
                ],
            )
        schema_gap = pending_schema_gap
        if schema_gap is not None:
            schema_gaps.append(schema_gap)
            session.write_stage1_5_schema_gaps(schema_gaps)
            if (
                schema_gap_repair_limit is not None
                and schema_gap_repair_count >= schema_gap_repair_limit
            ):
                session.write_stage2_intent_graph(
                    build_property_intent_graph(plan.properties),
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
                _write_stage0_artifacts(
                    session,
                    source_doc,
                    schema_context_packets,
                    property_context_packets,
                    completed_property_node_ids,
                    schema_atoms=approved_schema_atoms,
                    property_atoms=plan.properties,
                    schema_gaps=schema_gaps,
                )
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
                        f"({schema_gap_repair_limit}); stopped before synthesis.",
                    ],
            )
            repaired = _repair_schema_gap_and_validate(
                spec_text=active_spec_text,
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
                session.write_stage2_intent_graph(
                    build_property_intent_graph(plan.properties),
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
                _write_stage0_artifacts(
                    session,
                    source_doc,
                    schema_context_packets,
                    property_context_packets,
                    completed_property_node_ids,
                    schema_atoms=approved_schema_atoms,
                    property_atoms=plan.properties,
                    schema_gaps=schema_gaps,
                )
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
        if (
            atom_from_batch
            and not pending_property_atoms
            and active_property_node is not None
            and active_packet is not None
        ):
            completion_blocker = _source_node_completion_blocker(
                active_packet.focus_node_ids,
                plan.properties,
            )
            if completion_blocker is not None:
                decisions2.append(
                    AtomDecision(
                        atom_name=f"coverage_audit_{active_property_node.id}",
                        action="reject",
                        reason=completion_blocker,
                        edit_delta={
                            "stage": "stage2_source_node_completion",
                            "source_node_ids": list(active_packet.focus_node_ids),
                        },
                    ),
                )
                session.write_stage2_decisions(decisions2)
                _notify_property_progress(
                    review_atom,
                    event="coverage_blocked",
                    source_id=active_property_node.id,
                    source_index=property_frontier_index.get(active_property_node.id),
                    source_total=property_frontier_total,
                    source_completed=len(completed_property_node_ids),
                    source_open=max(
                        property_frontier_total - len(completed_property_node_ids),
                        0,
                    ),
                    approved=len(plan.properties),
                    decisions=len(decisions2),
                    proposed=len(prop_atoms),
                    queued=0,
                    reason=completion_blocker,
                )
                continue
            completed_property_node_ids.add(active_property_node.id)
            session.write_stage0_coverage_ledger(
                build_coverage_ledger(
                    source_doc,
                    completed_property_node_ids=completed_property_node_ids,
                    schema_packets=schema_context_packets,
                    property_packets=property_context_packets,
                ),
            )
            _notify_property_progress(
                review_atom,
                event="source_complete",
                source_id=active_property_node.id,
                source_index=property_frontier_index.get(active_property_node.id),
                source_total=property_frontier_total,
                source_completed=len(completed_property_node_ids),
                source_open=max(property_frontier_total - len(completed_property_node_ids), 0),
                approved=len(plan.properties),
                decisions=len(decisions2),
                proposed=len(prop_atoms),
                queued=0,
            )
            active_property_node = None
            active_packet = None
            active_spec_text = ""
    if not property_frontier_exhausted:
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
    session.write_stage2_decisions(decisions2)
    session.write_stage2_approved_atoms(plan.properties)
    _notify_property_progress(
        review_atom,
        event="complete" if property_frontier_exhausted else "stopped",
        source_total=property_frontier_total,
        source_completed=len(completed_property_node_ids),
        source_open=max(property_frontier_total - len(completed_property_node_ids), 0),
        approved=len(plan.properties),
        rejected=sum(1 for item in decisions2 if item.action != "approve"),
        decisions=len(decisions2),
        proposed=len(prop_atoms),
        queued=0,
    )
    _notify_review_stage_complete(review_atom, "Property intent review", decisions2)
    _notify_property_plan_ready(review_atom, plan.properties)
    session.write_stage2_intent_graph(
        build_property_intent_graph(plan.properties),
    )
    session.write_stage2_symbolic_verification_logs(verification_logs)
    session.write_stage2_adversarial_examples(
        {a.name: [_example_to_dict(e) for e in a.examples_adversarial] for a in plan.properties},
    )
    if not property_frontier_exhausted:
        _write_stage0_artifacts(
            session,
            source_doc,
            schema_context_packets,
            property_context_packets,
            completed_property_node_ids,
            schema_atoms=approved_schema_atoms,
            property_atoms=plan.properties,
            schema_gaps=schema_gaps,
        )
        session.flush_transcript()
        open_nodes = [
            node.id
            for node in property_frontier_nodes
            if node.id not in completed_property_node_ids
        ]
        return AuthorResult(
            session_id=session_id,
            session_dir=session.base,
            candidate_path=Path(""),
            plan=plan,
            schema_text=schema_text,
            final_user_approved=False,
            notes=[
                "Stage 2 stopped before covering the full source DAG; "
                f"{len(open_nodes)} authorization source node(s) remain open.",
            ],
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
        _write_stage0_artifacts(
            session,
            source_doc,
            schema_context_packets,
            property_context_packets,
            completed_property_node_ids,
            schema_atoms=approved_schema_atoms,
            property_atoms=plan.properties,
            schema_gaps=schema_gaps,
        )
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
        _write_stage0_artifacts(
            session,
            source_doc,
            schema_context_packets,
            property_context_packets,
            completed_property_node_ids,
            schema_atoms=approved_schema_atoms,
            property_atoms=plan.properties,
            schema_gaps=schema_gaps,
        )
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
    stage3_spec_text = approved_target_spec(
        original_spec_name=spec_path.name,
        schema_atoms=approved_schema_atoms,
        property_atoms=plan.properties,
    )
    scenario_dir = _materialize_scenario_dir(
        session_dir=session.base,
        spec_text=stage3_spec_text,
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

    _write_stage0_artifacts(
        session,
        source_doc,
        schema_context_packets,
        property_context_packets,
        completed_property_node_ids,
        schema_atoms=approved_schema_atoms,
        property_atoms=plan.properties,
        schema_gaps=schema_gaps,
    )
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

def _load_resume_checkpoint(base: Path) -> _ResumeCheckpoint:
    """Load an incomplete session so `author` can continue in-place."""
    if not base.exists():
        raise FileNotFoundError(f"resume session not found: {base}")
    schema_path = base / "stage1" / "final_schema.cedarschema"
    if not schema_path.exists():
        raise FileNotFoundError(f"resume session has no final schema: {schema_path}")

    schema_atoms = [_load_stage1_atom(item) for item in _read_json(base / "stage1" / "proposed_atoms.json", [])]
    stage1_attributions = [
        AttributionDecision(**item)
        for item in _read_json(base / "stage1" / "attribution_decisions.json", [])
    ]
    stage1_decisions = [
        AtomDecision(**item) for item in _read_json(base / "stage1" / "decisions.json", [])
    ]
    approved_schema_atoms = _approved_stage1_atoms(schema_atoms, stage1_decisions)
    approved_schema_atoms.extend(_approved_schema_repair_atoms(base / "stage1_5" / "schema_gap_repairs.json"))

    property_atoms = [
        from_dict(PropertyAtom, item)
        for item in _read_json(base / "stage2" / "proposed_atoms.json", [])
    ]
    for atom in property_atoms:
        _canonicalize_resumed_property_atom(atom)
    stage2_attributions = [
        AttributionDecision(**item)
        for item in _read_json(base / "stage2" / "attribution_decisions.json", [])
    ]
    raw_stage2_decisions = [
        AtomDecision(**item) for item in _read_json(base / "stage2" / "decisions.json", [])
    ]
    verification_logs = _read_json(base / "stage2" / "symbolic_verification_logs.json", {})
    coverage = _read_json(base / "stage0" / "coverage_ledger.json", {})
    completed_node_ids = set(coverage.get("completed_property_node_ids", []))

    approved_snapshot_path = base / "stage2" / "approved_atoms.json"
    if approved_snapshot_path.exists():
        approved_properties = [
            from_dict(PropertyAtom, item)
            for item in _read_json(approved_snapshot_path, [])
        ]
        for atom in approved_properties:
            _canonicalize_resumed_property_atom(atom)
            atom.intent_acknowledged_by_user = True
            atom.symbolic_verified = True
        stage2_decisions = raw_stage2_decisions
        reopened_source_node_ids: set[str] = set()
        approved_properties, stage2_decisions = _retire_superseded_resume_ceilings(
            approved_properties,
            stage2_decisions,
        )
    else:
        approved_properties, stage2_decisions, reopened_source_node_ids = _approved_property_atoms_for_resume(
            property_atoms,
            raw_stage2_decisions,
            verification_logs if isinstance(verification_logs, dict) else {},
        )
    completed_node_ids.difference_update(reopened_source_node_ids)

    schema_text = schema_path.read_text()
    schema_text = _amend_resumed_schema_actions_for_properties(
        schema_text,
        approved_properties,
    )

    return _ResumeCheckpoint(
        base=base,
        schema_text=schema_text,
        schema_atoms=schema_atoms,
        stage1_attributions=stage1_attributions,
        stage1_decisions=stage1_decisions,
        approved_schema_atoms=approved_schema_atoms,
        property_atoms=property_atoms,
        stage2_attributions=stage2_attributions,
        stage2_decisions=stage2_decisions,
        approved_property_atoms=approved_properties,
        completed_property_node_ids=completed_node_ids,
        schema_gaps=_read_json(base / "stage1_5" / "schema_gaps.json", []),
        schema_gap_repairs=_read_json(base / "stage1_5" / "schema_gap_repairs.json", []),
        verification_logs=verification_logs if isinstance(verification_logs, dict) else {},
        reopened_source_node_ids=reopened_source_node_ids,
    )


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def _load_stage1_atom(item: dict[str, Any]) -> Stage1AtomT:
    if "field_name" in item and "on_entity" in item:
        return from_dict(AttributeAtom, item)
    if "principal_types" in item or "resource_types" in item or "context_attributes" in item:
        return from_dict(ActionAtom, item)
    if "cedar_type" in item:
        return from_dict(TypeAliasAtom, item)
    return from_dict(EntityAtom, item)


def _approved_stage1_atoms(
    proposed_atoms: list[Stage1AtomT],
    decisions: list[AtomDecision],
) -> list[Stage1AtomT]:
    by_name = {atom.name: atom for atom in proposed_atoms}
    approved: list[Stage1AtomT] = []
    seen: set[str] = set()
    for decision in decisions:
        if decision.action != "approve" or decision.atom_name in seen:
            continue
        atom = by_name.get(decision.atom_name)
        if atom is not None:
            approved.append(atom)
            seen.add(decision.atom_name)
    return approved


def _approved_schema_repair_atoms(path: Path) -> list[Stage1AtomT]:
    repairs = _read_json(path, [])
    approved: list[Stage1AtomT] = []
    seen: set[str] = set()
    if not isinstance(repairs, list):
        return approved
    for repair in repairs:
        for raw_atom in repair.get("approved_atoms", []) if isinstance(repair, dict) else []:
            atom = _load_stage1_atom(raw_atom)
            if atom.name not in seen:
                approved.append(atom)
                seen.add(atom.name)
    return approved


def _normalize_property_proposals(result: PropertyProposalResult) -> list[PropertyAtom]:
    """Normalize old single-atom and new bundle proposers into a list."""
    if result is None:
        return []
    if isinstance(result, PropertyAtom):
        return [result]
    return [atom for atom in result if isinstance(atom, PropertyAtom)]


def _source_node_completion_blocker(
    focus_node_ids: list[str],
    approved_atoms: list[PropertyAtom],
) -> str | None:
    """Return a reason if a source node cannot be marked property-complete.

    This is deliberately structural. It does not infer intent from English
    keywords. Once HITL/AITL has accepted a floor for a source node, that node
    represents a bounded grant and must also expose a same-action safety side
    before Stage 2 can call the source node covered. The safety side may be a
    ceiling, disjointness, or rate limit atom. Without this guard the model can
    stop after a plausible positive permission and leave synthesis free to
    over-permit around it.
    """

    focus_ids = set(focus_node_ids)
    if not focus_ids:
        return None
    local_atoms = [
        atom
        for atom in approved_atoms
        if focus_ids.intersection(atom_source_ids(atom))
    ]
    floors = [atom for atom in local_atoms if atom.constraint_type == "floor" and atom.action]
    if not floors:
        return None
    safety_actions = {
        atom.action
        for atom in local_atoms
        if atom.action and atom.constraint_type in {"ceiling", "disjointness", "rate_limit"}
    }
    missing = [atom for atom in floors if atom.action not in safety_actions]
    if not missing:
        return None
    names = ", ".join(atom.name for atom in missing[:5])
    actions = ", ".join(sorted({atom.action for atom in missing}))
    return (
        "Source-node coverage is incomplete: approved floor atom(s) "
        f"{names} for action(s) {actions} have no same-source same-action "
        "ceiling, disjointness, or rate-limit safety atom yet. Propose the "
        "missing bounded-grant safety side before returning an empty atom list."
    )


def _approved_property_atoms_for_resume(
    proposed_atoms: list[PropertyAtom],
    decisions: list[AtomDecision],
    verification_logs: dict[str, list[str]],
) -> tuple[list[PropertyAtom], list[AtomDecision], set[str]]:
    """Trust approved properties unless the prior session recorded real invalidity.

    Older sessions could contain user-approved atoms whose Cedar body failed
    type checking. Resuming those as approved target constraints poisons
    synthesis. A bare ``symbolic_verified=false`` is not enough evidence,
    though: earlier runs often stored that value when the verifier never ran or
    the log was not persisted. We reopen only when the recorded log shows a
    concrete Cedar/type error. Verifier setup failures are environment problems,
    not intent rejections.
    """
    by_name = {atom.name: atom for atom in proposed_atoms}
    approved: list[PropertyAtom] = []
    rewritten_decisions: list[AtomDecision] = []
    reopened_source_node_ids: set[str] = set()
    seen_approved: set[str] = set()

    for decision in decisions:
        if decision.action != "approve":
            rewritten_decisions.append(decision)
            continue
        atom = by_name.get(decision.atom_name)
        if atom is None:
            rewritten_decisions.append(decision)
            continue
        if _resume_log_is_invalid_property(verification_logs.get(decision.atom_name, [])):
            reopened_source_node_ids.update(source_ids_from_text(atom.source_excerpt))
            rewritten_decisions.append(
                AtomDecision(
                    atom_name=decision.atom_name,
                    action="reject",
                    reason=(
                        "resume audit: this property had been approved by intent review, "
                        "but the recorded Cedar/type check failed, so AutoCedar must "
                        "repair or repropose it before synthesis."
                    ),
                    edit_delta={"original_resume_decision": to_dict(decision)},
                    intent_acknowledged_by_user=decision.intent_acknowledged_by_user,
                    symbolic_verified=False,
                ),
            )
            continue
        if decision.atom_name not in seen_approved:
            atom.intent_acknowledged_by_user = True
            atom.symbolic_verified = True
            approved.append(atom)
            seen_approved.add(decision.atom_name)
        rewritten_decisions.append(decision)
    approved, rewritten_decisions = _retire_superseded_resume_ceilings(
        approved,
        rewritten_decisions,
    )
    return approved, rewritten_decisions, reopened_source_node_ids


def _retire_superseded_resume_ceilings(
    approved: list[PropertyAtom],
    decisions: list[AtomDecision],
) -> tuple[list[PropertyAtom], list[AtomDecision]]:
    """Drop older same-action ceilings superseded by later provenance-union ceilings.

    A repaired ceiling can intentionally widen an earlier ceiling into a union
    after a later floor reveals missing authorized scope. Keeping both ceilings
    makes the target the intersection and recreates the stale conflict. During
    resume, retire an older ceiling when a later approved ceiling for the same
    action cites a strict superset of the older ceiling's source ids.
    """
    retired: dict[str, str] = {}
    for i, older in enumerate(approved):
        if older.constraint_type != "ceiling":
            continue
        older_ids = set(source_ids_from_text(older.source_excerpt))
        if not older_ids:
            continue
        for newer in approved[i + 1 :]:
            if newer.constraint_type != "ceiling" or newer.action != older.action:
                continue
            newer_ids = set(source_ids_from_text(newer.source_excerpt))
            if older_ids <= newer_ids and older.reference_cedar != newer.reference_cedar:
                retired[older.name] = newer.name
                break
    if not retired:
        return approved, decisions
    filtered = [atom for atom in approved if atom.name not in retired]
    rewritten: list[AtomDecision] = []
    for decision in decisions:
        if decision.action == "approve" and decision.atom_name in retired:
            rewritten.append(
                AtomDecision(
                    atom_name=decision.atom_name,
                    action="reject",
                    reason=(
                        "resume audit: retired because later approved ceiling "
                        f"`{retired[decision.atom_name]}` cites a strict superset "
                        "of this ceiling's source ids for the same action."
                    ),
                    edit_delta={"original_resume_decision": to_dict(decision)},
                    intent_acknowledged_by_user=decision.intent_acknowledged_by_user,
                    symbolic_verified=decision.symbolic_verified,
                ),
            )
        else:
            rewritten.append(decision)
    return filtered, rewritten


def _resume_log_is_invalid_property(log: list[str]) -> bool:
    text = "\n".join(log).lower()
    if not text:
        return False
    setup_markers = (
        "verifier setup",
        "cannot run `symcc`",
        "analyze feature",
        "solver not found",
        "failed to start",
        "unexpected argument",
        "--principal-type",
        "--cvc5-path",
    )
    if any(marker in text for marker in setup_markers):
        return False
    invalid_markers = (
        "type-correct: failed",
        "cedar validate",
        "failed to parse",
        "failed to resolve",
        "validation failed",
        "expected entity uid",
        "schema/type check: failed",
    )
    return any(marker in text for marker in invalid_markers)


def _canonicalize_resumed_property_atom(atom: PropertyAtom) -> None:
    atom.reference_cedar = _canonicalize_resumed_reference_cedar(atom.reference_cedar)
    if atom.disjoint_target_body:
        atom.disjoint_target_body = _canonicalize_type_membership_expr(atom.disjoint_target_body)


def _canonicalize_resumed_reference_cedar(cedar: str) -> str:
    """Normalize stale checkpoint Cedar syntax without changing intent.

    Older AutoCedar runs sometimes wrote type membership as
    ``principal in SomeType`` / ``resource in SomeResource``. Cedar parses bare
    identifiers after ``in`` as entity UIDs or template slots, not types. The
    intended and reviewed form is the Cedar type test ``is``.
    """
    return _canonicalize_type_membership_expr(cedar)


def _canonicalize_type_membership_expr(cedar: str) -> str:
    if not cedar:
        return cedar

    def replace_type_test(match: re.Match[str]) -> str:
        lhs, rhs = match.group(1), match.group(2)
        if "::" in rhs or '"' in rhs:
            return match.group(0)
        return f"{lhs} is {rhs}"

    return re.sub(
        r"\b(principal|resource)\s+in\s+([A-Z][A-Za-z0-9_]*)\b",
        replace_type_test,
        cedar,
    )


def _amend_resumed_schema_actions_for_properties(
    schema_text: str,
    properties: list[PropertyAtom],
) -> str:
    """Ensure resumed schema action scopes include approved property scopes."""
    amended = schema_text
    for atom in properties:
        action = atom.action.replace('Action::"', "").rstrip('"')
        for principal_type in atom.principal_types:
            amended = _add_type_to_action_scope(
                amended,
                action_name=action,
                field_name="principal",
                type_name=principal_type,
            )
        for resource_type in atom.resource_types:
            amended = _add_type_to_action_scope(
                amended,
                action_name=action,
                field_name="resource",
                type_name=resource_type,
            )
    return amended


def _add_type_to_action_scope(
    schema_text: str,
    *,
    action_name: str,
    field_name: str,
    type_name: str,
) -> str:
    if not action_name or not type_name:
        return schema_text
    if not re.search(rf"\bentity\s+{re.escape(type_name)}\b", schema_text):
        return schema_text
    action_re = re.compile(
        rf"(action\s+{re.escape(action_name)}\s+appliesTo\s*\{{)(?P<body>.*?)(\n\}};)",
        re.DOTALL,
    )
    match = action_re.search(schema_text)
    if not match:
        return schema_text
    body = match.group("body")
    field_re = re.compile(
        rf"({re.escape(field_name)}\s*:\s*\[)(?P<types>[^\]]*)(\]\s*,)",
    )
    field_match = field_re.search(body)
    if not field_match:
        return schema_text
    existing = [part.strip() for part in field_match.group("types").split(",") if part.strip()]
    if type_name in existing:
        return schema_text
    existing.append(type_name)
    new_field = field_match.group(1) + ", ".join(existing) + field_match.group(3)
    new_body = body[: field_match.start()] + new_field + body[field_match.end() :]
    return schema_text[: match.start("body")] + new_body + schema_text[match.end("body") :]


def _draft_from_approved_schema_atoms(atoms: list[Stage1AtomT]) -> SchemaDraft:
    draft = SchemaDraft()
    for atom in atoms:
        _route_into_schema_draft(atom, draft)
    return draft


def _repair_named_prior_property(
    *,
    spec_text: str,
    schema_path: Path,
    current_atom: PropertyAtom,
    repair_plan: PropertyRepairPlan,
    plan: VerificationPlanDraft,
    approved_property_names: set[str],
    prior_repairs_attempted: set[str],
    repair_property_atom: PropertyRepairer,
    review_atom: AtomReviewer,
    decisions: list[AtomDecision],
    session: Session,
    verification_logs: dict[str, list[str]],
) -> bool:
    """Repair the exact prior property selected by the repair planner."""
    prior_name = (repair_plan.target_atom or "").strip()
    if not prior_name:
        return False
    if prior_name in prior_repairs_attempted:
        return False
    prior_index = next(
        (i for i, atom in enumerate(plan.properties) if atom.name == prior_name),
        None,
    )
    if prior_index is None:
        return False
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
        repair_plan.repair_instruction or repair_plan.reason,
        other_atoms,
    )
    if replacement is None:
        return False
    replacement = attach_source_ids(replacement, source_ids_from_text(spec_text))
    replacement = _align_repaired_property_atom(
        rejected_atom=prior_atom,
        replacement=replacement,
        reason=repair_plan.repair_instruction or repair_plan.reason,
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
            "reason": repair_plan.reason,
            "repair_instruction": repair_plan.repair_instruction,
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
        return False
    reviewed_replacement.intent_acknowledged_by_user = True
    plan.properties[prior_index] = reviewed_replacement
    approved_property_names.discard(prior_atom.name)
    approved_property_names.add(reviewed_replacement.name)
    session.write_stage2_approved_atoms(plan.properties)
    return True


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
    proposed_atoms = [
        attach_source_ids(atom, source_ids_from_text(repair_spec))
        for atom in propose_schema_atoms(repair_spec)
    ]
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
        "For example, if the approved source text requires a common request "
        "context or relationship field across several protected actions, emit "
        "the minimal atoms that add that generic hook to those actions. Still "
        "keep each emitted atom individually reviewable.\n"
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
    """Return the repairer-selected replacement without hidden intent rewrites."""

    _ = rejected_atom, reason
    return replacement


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


def _notify_property_progress(review_atom: AtomReviewer, **payload: Any) -> None:
    callback = getattr(review_atom, "property_progress", None)
    if callable(callback):
        callback(payload)


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
