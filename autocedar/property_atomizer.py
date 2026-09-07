"""Stage 2 LLM property atomization."""

from __future__ import annotations

from pathlib import Path

from autocedar.atoms import PropertyAtom
from autocedar.corpus import AtomDecision
from autocedar.llm import LLMClient


def propose_property_atom(
    spec_text: str,
    schema_path: str,
    llm: LLMClient,
    prior_atoms: list[PropertyAtom],
    prior_decisions: list[AtomDecision],
) -> list[PropertyAtom]:
    """Propose a local Stage 2 property bundle from spec, schema, and review history.

    The pipeline still reviews each returned atom individually. Returning a
    bundle only avoids repeated model round trips for the same source packet.
    """
    schema_text = Path(schema_path).read_text()
    return llm.propose_property_atoms(
        spec_text,
        schema_text,
        prior_atoms=prior_atoms,
        prior_decisions=prior_decisions,
    )


def plan_property_repair(text, schema_path, current_atom, decision, prior_atoms,
                         schema_text, symbolic_log, *, llm: LLMClient):
    """Shared CLI/TUI repair routing; never use the test fallback in the UI."""
    from autocedar.pipeline import PropertyRepairPlan

    response = llm.plan_property_rejection(
        current_atom=current_atom, user_reason=decision.reason, spec_text=text,
        schema_text=schema_text, prior_atoms=prior_atoms, symbolic_log=symbolic_log,
    )
    return PropertyRepairPlan(
        action=response.action, target_atom=response.target_atom,
        reason=response.reason, repair_instruction=response.repair_instruction,
        schema_gap_summary=response.schema_gap_summary,
    )
