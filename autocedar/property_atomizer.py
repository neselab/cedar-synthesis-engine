"""Stage 2 LLM property atomization."""

from __future__ import annotations

from pathlib import Path

from autocedar.atoms import PropertyAtom
from autocedar.llm import LLMClient


def propose_property_atoms(
    spec_text: str,
    schema_path: str,
    llm: LLMClient,
) -> list[PropertyAtom]:
    """Propose Stage 2 property atoms from a prose spec and validated schema."""
    schema_text = Path(schema_path).read_text()
    return llm.propose_property_atoms(spec_text, schema_text)
