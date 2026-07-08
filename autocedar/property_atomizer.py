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
