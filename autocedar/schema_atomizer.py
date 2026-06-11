"""Stage 1 — schema atomization.

See ``docs/HITL_STEP_B_PLAN.md`` §7.2 for the composition primitive
and ``docs/HITL_STEP_C_PLAN.md`` §3 (acceptance criteria 2–3) for the
LLM integration:

- ``propose_schema_atoms`` is a thin wrapper over ``LLMClient`` so the
  pipeline can stay pluggable and tests can inject any callable.
- ``compose_and_validate`` runs ``cedar validate`` after composition;
  on failure it asks the LLM to fix the schema and re-validates,
  bounded to ``max_attempts`` retries.
"""

from __future__ import annotations

import dataclasses
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from autocedar.atoms import (
    ActionAtom,
    AttributeAtom,
    EntityAtom,
    SchemaDraft,
    TypeAliasAtom,
)
from autocedar.llm import LLMClient, Stage1Atom

CEDAR_PATH = os.environ.get("CEDAR", os.path.expanduser("~/.cargo/bin/cedar"))


def _render_attribute(attr: AttributeAtom, indent: str = "    ") -> str:
    optional_marker = "?" if attr.optional else ""
    return f"{indent}{attr.field_name}{optional_marker}: {attr.cedar_type},"


def _render_entity(entity: EntityAtom) -> str:
    """Emit an ``entity X { ... };`` block.

    Falls back to ``entity X;`` (no body) when the atom has no
    attributes, members_of, or enum values.
    """
    lines: list[str] = []
    in_clause = ""
    if entity.members_of:
        in_clause = f" in [{', '.join(entity.members_of)}]"
    if entity.enum_values is not None:
        # Enumerated entity: `entity X enum ["a", "b", ...];`
        values = ", ".join(f'"{v}"' for v in entity.enum_values)
        return f"entity {entity.name} enum [{values}];"
    if not entity.attributes:
        return f"entity {entity.name}{in_clause};"
    lines.append(f"entity {entity.name}{in_clause} {{")
    for attr in entity.attributes.values():
        lines.append(_render_attribute(attr))
    lines.append("};")
    return "\n".join(lines)


def _render_action(action: ActionAtom) -> str:
    """Emit an ``action X appliesTo { ... };`` block."""
    parts: list[str] = []
    parts.append(f"action {action.name} appliesTo {{")
    if action.principal_types:
        parts.append(
            f"    principal: [{', '.join(action.principal_types)}],"
        )
    if action.resource_types:
        parts.append(
            f"    resource: [{', '.join(action.resource_types)}],"
        )
    if action.context_attributes:
        parts.append("    context: {")
        for attr in action.context_attributes.values():
            parts.append(_render_attribute(attr, indent="        "))
        parts.append("    },")
    parts.append("};")
    return "\n".join(parts)


def _render_type_alias(alias: TypeAliasAtom) -> str:
    return f"type {alias.name} = {alias.cedar_type};"


def compose_schema(draft: SchemaDraft) -> str:
    """Render a ``SchemaDraft`` to ``.cedarschema`` text.

    Output ordering: type aliases first, then entities, then actions —
    so forward references inside entity attributes resolve to the
    aliases declared above. Within each section, items appear in
    insertion order (not sorted) so authors can control ordering.
    """
    blocks: list[str] = []
    for alias in draft.type_aliases.values():
        blocks.append(_render_type_alias(alias))
    for entity in draft.entities.values():
        blocks.append(_render_entity(entity))
    for action in draft.actions.values():
        blocks.append(_render_action(action))
    return "\n\n".join(blocks) + "\n"


# ---------------------------------------------------------------------------
# LLM integration.
# ---------------------------------------------------------------------------

@dataclass
class ComposeAndValidateResult:
    """Output of ``compose_and_validate``.

    ``attempts`` records what happened on each loop iteration so the
    corpus log can later study how often the LLM-fix loop succeeds and
    on which kinds of validator errors.
    """

    schema_text: str
    schema_path: Path
    succeeded: bool
    attempts: list["FixAttempt"] = field(default_factory=list)


@dataclass
class FixAttempt:
    """One iteration of the compose-validate-fix loop."""

    attempt_number: int
    schema_text: str
    validator_passed: bool
    validator_error: str = ""
    llm_was_called: bool = False


def propose_schema_atoms(
    spec_text: str, llm: LLMClient,
) -> list[Stage1Atom]:
    """Stage 1 atom proposer (thin wrapper over LLMClient).

    Returns the LLM's proposed atoms as typed dataclasses (already
    translated from the Pydantic LLM schema). The pipeline consumes this
    list and dispatches each atom to the review loop.
    """
    return llm.propose_schema_atoms(spec_text)


def route_atom_into_draft(atom: Stage1Atom, draft: SchemaDraft) -> None:
    """Insert one approved atom into the right SchemaDraft slot.

    Attribute atoms target an entity by ``on_entity`` name; if the
    owner entity is not yet in the draft, the attribute is dropped
    silently. The corpus log captures the decision separately so the user
    can detect this case during review.
    """
    if isinstance(atom, EntityAtom):
        draft.entities[atom.name] = atom
    elif isinstance(atom, ActionAtom):
        draft.actions[atom.name] = atom
    elif isinstance(atom, TypeAliasAtom):
        draft.type_aliases[atom.name] = atom
    elif isinstance(atom, AttributeAtom):
        owner = draft.entities.get(atom.on_entity)
        if owner is not None:
            owner.attributes[atom.field_name] = atom


def cedar_validate_schema(schema_path: Path) -> tuple[bool, str]:
    """Run ``cedar validate`` on a schema. Returns ``(ok, error_msg)``."""
    try:
        result = subprocess.run(
            [CEDAR_PATH, "validate", "--schema", str(schema_path), "--policies", "/dev/null"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return False, "cedar validate timed out"
    except FileNotFoundError:
        return False, f"cedar binary not found at {CEDAR_PATH}"
    if result.returncode == 0:
        return True, ""
    # Cedar 4.10 emits diagnostic text on stderr.
    return False, (result.stderr.strip() or result.stdout.strip())


def compose_and_validate(
    draft: SchemaDraft,
    schema_path: Path,
    llm: Optional[LLMClient] = None,
    spec_text: str = "",
    max_attempts: int = 3,
) -> ComposeAndValidateResult:
    """Compose the schema, validate it, and (if invalid) ask the LLM to fix.

    Per HITL_STEP_C_PLAN.md acceptance criterion 3:

    - Try 1: compose from the draft, write to ``schema_path``, run
      ``cedar validate``. If it passes, return.
    - Tries 2–``max_attempts``: pass the validator's error to
      ``llm.fix_schema()`` (along with the spec, so the model has
      grounding) and re-validate. The returned text replaces the
      previous schema text on disk.
    - On exhaustion: return ``succeeded=False`` with the attempt log
      populated.

    The ``llm`` parameter is optional. When ``None``, validation
    failure simply returns ``succeeded=False`` without any LLM call —
    used by tests that want to exercise the validator path in
    isolation.
    """
    schema_path = Path(schema_path)
    schema_path.parent.mkdir(parents=True, exist_ok=True)

    schema_text = compose_schema(draft)
    schema_path.write_text(schema_text)

    attempts: list[FixAttempt] = []

    for attempt_number in range(1, max_attempts + 1):
        passed, error = cedar_validate_schema(schema_path)
        attempts.append(
            FixAttempt(
                attempt_number=attempt_number,
                schema_text=schema_text,
                validator_passed=passed,
                validator_error="" if passed else _trim_error(error),
                llm_was_called=False,
            ),
        )
        if passed:
            return ComposeAndValidateResult(
                schema_text=schema_text,
                schema_path=schema_path,
                succeeded=True,
                attempts=attempts,
            )

        if llm is None or attempt_number == max_attempts:
            # Final attempt failed (or no LLM provided) — return failure.
            return ComposeAndValidateResult(
                schema_text=schema_text,
                schema_path=schema_path,
                succeeded=False,
                attempts=attempts,
            )

        # Ask the LLM to fix the schema. Mark the next attempt as
        # llm_was_called by mutating its entry once it lands.
        fixed_text = llm.fix_schema(
            schema_text=schema_text,
            cedar_error_message=error,
            spec_text=spec_text,
        )
        # Strip any Markdown fencing the LLM may add despite the
        # Pydantic schema. ``fix_schema`` returns the inner text, but
        # be defensive.
        schema_text = _strip_code_fence(fixed_text)
        schema_path.write_text(schema_text)
        # Tag the *next* attempt's record with llm_was_called=True.
        # The loop overwrites the entry on the next pass; mark a
        # parallel entry here so the log captures both the failure and
        # the fix attempt cleanly.
        attempts[-1] = dataclasses.replace(attempts[-1], llm_was_called=True)

    # Unreachable — the loop above always returns or continues.
    raise RuntimeError("compose_and_validate exhausted max_attempts unexpectedly")


_CODE_FENCE_RE = re.compile(
    r"^\s*```(?:cedarschema|cedar|schema|.*)?\s*\n(.*?)\n```\s*$",
    re.DOTALL,
)


def _strip_code_fence(text: str) -> str:
    """Strip a leading/trailing Markdown code fence if the LLM added one."""
    m = _CODE_FENCE_RE.match(text)
    if m is None:
        return text
    return m.group(1)


def _trim_error(error: str, max_chars: int = 600) -> str:
    """Trim long validator errors to the first ~600 chars so corpus logs
    stay readable."""
    if len(error) <= max_chars:
        return error
    return error[:max_chars] + "..."
