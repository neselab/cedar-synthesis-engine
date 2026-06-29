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
from autocedar.source_doc import (
    attach_source_ids,
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

# Stage 2: propose the next property atom from prose + schema + review history.
PropertyProposer = Callable[
    [str, str, list[PropertyAtom], list[AtomDecision]],
    Optional[PropertyAtom],
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
) -> Optional[PropertyAtom]:
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
    schema_gaps: list[dict[str, Any]] = []
    schema_gap_repairs: list[dict[str, Any]] = []
    schema_gap_repair_count = 0
    schema_gap_repair_limit = max_schema_gap_repairs

    spec_text = spec_path.read_text()
    session.write_input_spec(spec_text, filename=spec_path.name)
    source_doc = compile_source_document(spec_text)
    session.write_stage0_source_index(source_doc.to_index())
    schema_context_packets = []
    property_context_packets = []
    completed_property_node_ids: set[str] = set()
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
    prop_atoms: list[PropertyAtom] = []
    attributions2: list[AttributionDecision] = []
    decisions2: list[AtomDecision] = []
    plan = VerificationPlanDraft(properties=[])
    verification_logs: dict[str, list[str]] = {}
    repair_plans: list[dict[str, Any]] = []
    incremental_candidates: list[dict[str, Any]] = []
    approved_property_names: set[str] = set()
    property_frontier_nodes = source_doc.authorization_nodes()
    active_property_node = None
    property_frontier_exhausted = False
    _notify_review_stage(review_atom, "Property intent review", None)
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
        atom = propose_property_atom(
            active_spec_text,
            str(schema_path),
            plan.properties,
            decisions2,
        )
        if atom is not None:
            atom = attach_source_ids(atom, active_packet.node_ids())
        if atom is None:
            completed_property_node_ids.add(active_property_node.id)
            session.write_stage0_coverage_ledger(
                build_coverage_ledger(
                    source_doc,
                    completed_property_node_ids=completed_property_node_ids,
                    schema_packets=schema_context_packets,
                    property_packets=property_context_packets,
                ),
            )
            active_property_node = None
            continue
        prop_atoms.append(atom)
        attributions2.append(
            AttributionDecision(atom_name=atom.name, span_text=atom.source_excerpt),
        )
        session.write_stage2_proposed_atoms(prop_atoms)
        session.write_stage2_attribution_decisions(attributions2)
        if atom.name in approved_property_names:
            decisions2.append(_duplicate_decision(atom.name, "property"))
            completed_property_node_ids.add(active_property_node.id)
            active_property_node = None
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
                    replacement = attach_source_ids(replacement, active_packet.node_ids())
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
