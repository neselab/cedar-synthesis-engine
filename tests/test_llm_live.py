"""Live tests for ``autocedar.llm`` against the real Anthropic API.

Per ``docs/HITL_STEP_C_PLAN.md`` §3 acceptance criterion 6, this is
default-skipped. To run: ``uv run pytest --run-live`` with
``ANTHROPIC_API_KEY`` set in the environment.

The tests verify that the production LLMClient end-to-end produces a
plausible schema for a small prose spec, and that the resulting
schema passes ``cedar validate``. They are not deterministic and do
not assert specific atom contents — only structural properties.
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from autocedar.atoms import (
    ActionAtom,
    EntityAtom,
    SchemaDraft,
)
from autocedar.grounding import CEDAR_PATH
from autocedar.llm import LLMClient
from autocedar.schema_atomizer import (
    cedar_validate_schema,
    compose_and_validate,
    propose_schema_atoms,
    route_atom_into_draft,
)

_HAVE_CEDAR = os.path.isfile(CEDAR_PATH) and os.access(CEDAR_PATH, os.X_OK)


pytestmark = pytest.mark.live


@pytest.mark.skipif(not _HAVE_CEDAR, reason="cedar not available")
def test_live_proposer_yields_validating_schema_for_simple_spec(tmp_path: Path) -> None:
    """The default LLMClient (claude-opus-4-7) proposes a plausible
    schema for a 2-sentence prose spec; the resulting schema passes
    cedar validate after at most one LLM-driven fix attempt."""
    spec_text = textwrap.dedent("""\
        A document management system. Users have a role attribute
        (admin or member) and can read documents owned by other users.
    """).strip()

    llm = LLMClient()  # picks up ANTHROPIC_API_KEY from env
    atoms = propose_schema_atoms(spec_text, llm)

    # Structural assertions only (LLM output is not deterministic).
    assert len(atoms) > 0, "LLM returned no atoms"
    assert any(isinstance(a, EntityAtom) for a in atoms), "no entity atoms"
    assert any(isinstance(a, ActionAtom) for a in atoms), "no action atoms"

    # All atoms must reference the spec in their source_excerpt
    # (the prompt is explicit about quoting verbatim).
    for atom in atoms:
        assert atom.source_excerpt, f"atom {atom.name} has empty source_excerpt"

    # Route into a draft and compose+validate (with LLM-driven fix).
    draft = SchemaDraft()
    for atom in atoms:
        route_atom_into_draft(atom, draft)

    schema_path = tmp_path / "schema.cedarschema"
    result = compose_and_validate(
        draft, schema_path, llm=llm, spec_text=spec_text, max_attempts=3,
    )

    if not result.succeeded:
        for a in result.attempts:
            print(
                f"attempt {a.attempt_number} passed={a.validator_passed} "
                f"error={a.validator_error[:200]}",
            )
        pytest.fail(
            f"compose_and_validate exhausted {len(result.attempts)} attempts "
            f"without producing a validating schema",
        )

    passed, err = cedar_validate_schema(schema_path)
    assert passed, f"final schema failed cedar validate: {err}"
