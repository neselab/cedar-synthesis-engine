"""Stage 2 — property elicitation and sugar compile-down.

The LLM-backed property atom proposer lives in ``autocedar.property_atomizer``.
This module takes approved property atoms and compiles them into the concrete
v1-harness artifacts used by symbolic synthesis:

- ``compile_plan(plan)`` resolves all sugar atoms into primitive
  ceiling/floor/liveness checks, applies §8.8 patches from
  disjointness atoms to every same-action floor, and emits the
  ``verification_plan.py`` + ``references/*.cedar`` artifacts the v1
  harness consumes.

- Cedar text manipulation primitives (``wrap_when_with_conjuncts``,
  ``insert_when_with_conjuncts``) used by the §8.8 patcher.

The compiled output is byte-deterministic so it can be golden-tested
and reviewed.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass

from autocedar.atoms import (
    PropertyAtom,
    VerificationPlanDraft,
)


# ---------------------------------------------------------------------------
# Compile-down result.
# ---------------------------------------------------------------------------

@dataclass
class CompiledPlan:
    """Output of ``compile_plan``: harness-ready artifacts.

    ``verification_plan_py`` is the full text of ``verification_plan.py``
    (the file with ``get_checks()``). ``references`` maps reference
    names to their Cedar text bodies — to be written to
    ``references/<name>.cedar``.
    """

    verification_plan_py: str
    references: dict[str, str]


# ---------------------------------------------------------------------------
# Cedar text manipulation primitives.
# ---------------------------------------------------------------------------

_WHEN_RE = re.compile(r"\bwhen\s*\{")


def _find_when_block(policy_text: str) -> tuple[int, int, int] | None:
    """Locate the first ``when { ... }`` block.

    Returns ``(when_start, brace_open, brace_close)`` indices, or ``None``
    if no ``when {`` block is present. ``brace_close`` is the index of
    the matching ``}``. Brace counting respects nested braces (e.g.
    record literals inside the body).
    """
    m = _WHEN_RE.search(policy_text)
    if m is None:
        return None
    when_start = m.start()
    brace_open = m.end() - 1  # index of the '{'
    depth = 1
    i = brace_open + 1
    while i < len(policy_text) and depth > 0:
        ch = policy_text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    if depth != 0:
        raise ValueError("Unbalanced braces in `when { ... }` block")
    brace_close = i - 1
    return when_start, brace_open, brace_close


def wrap_when_with_conjuncts(policy_text: str, conjuncts: list[str]) -> str:
    """Append additional ``&&``-joined conjuncts to the ``when`` clause.

    Wraps the existing body in parens to preserve precedence. If the
    policy has no ``when`` clause, one is inserted before the trailing
    ``;``. Each conjunct is rendered on its own line for readability.

    Note: comments inside the original ``when`` body are preserved.
    """
    if not conjuncts:
        return policy_text
    block = _find_when_block(policy_text)
    if block is None:
        return insert_when_with_conjuncts(policy_text, conjuncts)
    when_start, brace_open, brace_close = block
    inner = policy_text[brace_open + 1 : brace_close]
    body = inner.strip()
    new_body = "(" + body + ")"
    for c in conjuncts:
        new_body += "\n    && " + c
    return (
        policy_text[: brace_open + 1]
        + "\n    "
        + new_body
        + "\n"
        + policy_text[brace_close:]
    )


def insert_when_with_conjuncts(policy_text: str, conjuncts: list[str]) -> str:
    """Insert a fresh ``when { ... }`` clause into a policy that has none.

    Splices in before the trailing ``;``. Conjuncts are joined with
    ``&&`` on separate lines.
    """
    if not conjuncts:
        return policy_text
    body = "\n    ".join(conjuncts) if len(conjuncts) == 1 else (
        "\n    && ".join(conjuncts)
    )
    # The first conjunct should not have a leading "&&".
    body = "\n    " + conjuncts[0]
    for c in conjuncts[1:]:
        body += "\n    && " + c
    semicolon = policy_text.rfind(";")
    if semicolon == -1:
        # Best-effort: append at end.
        return policy_text + "\nwhen {" + body + "\n};"
    return (
        policy_text[:semicolon].rstrip()
        + "\nwhen {"
        + body
        + "\n}"
        + policy_text[semicolon:]
    )


# ---------------------------------------------------------------------------
# §8.8 patch application.
# ---------------------------------------------------------------------------

def _collect_disjointness_patches(
    plan: VerificationPlanDraft,
) -> dict[str, list[tuple[str, str]]]:
    """For each action, list the (atom_name, negated_target_body) pairs to
    patch into every floor on that action.

    Returns: ``{action_name: [(disjointness_atom_name, "!(<body>)"), ...]}``.
    """
    out: dict[str, list[tuple[str, str]]] = {}
    for atom in plan.properties:
        if atom.constraint_type != "disjointness":
            continue
        if atom.disjoint_target_body is None:
            continue
        out.setdefault(atom.action, []).append(
            (atom.name, f"!({atom.disjoint_target_body})"),
        )
    return out


# ---------------------------------------------------------------------------
# Plan compilation.
# ---------------------------------------------------------------------------

def compile_plan(plan: VerificationPlanDraft) -> CompiledPlan:
    """Compile a verification plan: sugars → primitives, §8.8 patches applied.

    The output is deterministic byte-for-byte for a given input — the
    plan-rendering step uses fixed indentation, sorted keys where
    appropriate, and stable check ordering (preserving the input
    ``plan.properties`` list order).
    """
    patches_per_action = _collect_disjointness_patches(plan)

    references: dict[str, str] = {}
    plan_entries: list[dict] = []

    for atom in plan.properties:
        # 1. Compile to a primitive type for the harness contract.
        primitive_type = _resolve_primitive_type(atom)

        # 2. Build the plan entry (no reference text for liveness).
        entry: dict = {
            "name": atom.name,
            "description": atom.plain_english_summary,
            "type": primitive_type,
            "principal_type": _principal_type(atom),
            "action": _action_literal(atom),
            "resource_type": _resource_type(atom),
        }

        # 3. Compute the reference text (with §8.8 patches if applicable)
        #    and emit it under references/<name>.cedar.
        if primitive_type == "always-denies-liveness":
            # Liveness has no reference file in the v1 harness contract.
            plan_entries.append(entry)
            continue

        ref_cedar = atom.reference_cedar
        if primitive_type == "floor":
            patches = patches_per_action.get(atom.action, [])
            if patches:
                conjuncts = [body for _, body in patches]
                ref_cedar = wrap_when_with_conjuncts(ref_cedar, conjuncts)

        references[atom.name] = ref_cedar
        if primitive_type == "implies":
            entry["reference_path"] = f'os.path.join(REFS, "{atom.name}.cedar")'
        else:  # floor
            entry["floor_path"] = f'os.path.join(REFS, "{atom.name}.cedar")'

        plan_entries.append(entry)

    plan_text = _render_verification_plan_py(plan_entries)
    return CompiledPlan(
        verification_plan_py=plan_text,
        references=references,
    )


def _resolve_primitive_type(atom: PropertyAtom) -> str:
    """Map sugar atom types to harness-facing primitive type strings."""
    if atom.constraint_type == "ceiling":
        return "implies"
    if atom.constraint_type == "floor":
        return "floor"
    if atom.constraint_type == "liveness":
        return "always-denies-liveness"
    if atom.constraint_type == "rate_limit":
        # Compiles to a ceiling (implies).
        return "implies"
    if atom.constraint_type == "disjointness":
        # Compiles to a ceiling (implies).
        return "implies"
    raise ValueError(f"unknown constraint_type: {atom.constraint_type}")


def _principal_type(atom: PropertyAtom) -> str:
    if not atom.principal_types:
        return ""
    return atom.principal_types[0]


def _resource_type(atom: PropertyAtom) -> str:
    if not atom.resource_types:
        return ""
    return atom.resource_types[0]


def _action_literal(atom: PropertyAtom) -> str:
    """Render ``atom.action`` as a Cedar action literal.

    Accepts both ``"read"`` (bare) and ``Action::"read"`` (already-qualified)
    forms — bare forms are wrapped in ``Action::"..."``.
    """
    a = atom.action
    if a.startswith("Action::"):
        return a
    return f'Action::"{a}"'


# ---------------------------------------------------------------------------
# Rendering verification_plan.py.
# ---------------------------------------------------------------------------

def _render_verification_plan_py(entries: list[dict]) -> str:
    """Emit a verification_plan.py file matching the existing CedarBench shape.

    The file imports os, defines REFS, and exports get_checks() returning
    the list of dicts. Indentation is fixed (4 spaces).
    """
    header = textwrap.dedent(
        '''\
        """Verification plan generated by autocedar.property_elicitor.

        Sugar atoms (rate_limit, disjointness) have been compiled to
        primitive ceiling/floor/liveness checks per
        docs/HITL_STEP_B_PLAN.md §5. §8.8 floor-bound consistency
        patches from disjointness atoms have been applied to all
        same-action floors.
        """
        import os

        REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


        def get_checks():
            return [
        '''
    )

    body_lines: list[str] = []
    for entry in entries:
        body_lines.append("        {")
        body_lines.append(f'            "name": "{entry["name"]}",')
        body_lines.append(
            f'            "description": "{_escape_str(entry["description"])}",',
        )
        body_lines.append(f'            "type": "{entry["type"]}",')
        body_lines.append(f'            "principal_type": "{entry["principal_type"]}",')
        body_lines.append(f'            "action": "{_escape_str(entry["action"])}",')
        body_lines.append(f'            "resource_type": "{entry["resource_type"]}",')
        if "reference_path" in entry:
            body_lines.append(f'            "reference_path": {entry["reference_path"]},')
        if "floor_path" in entry:
            body_lines.append(f'            "floor_path": {entry["floor_path"]},')
        body_lines.append("        },")

    footer = "    ]\n"
    return header + "\n".join(body_lines) + "\n" + footer


def _escape_str(s: str) -> str:
    """Escape a string for safe inclusion in a Python double-quoted string literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"')
