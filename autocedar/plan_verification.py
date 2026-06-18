"""Plan-level verification: Stage 1.75 unsat detection + Stage 2.5 traceback.

See ``docs/HITL_STEP_B_PLAN.md`` §7.3 (Stage 1.75) and §7.4 (Stage 2.5)
for context. These checks run *between* the per-atom grounding (§4)
and the v1 harness invocation (§7.5):

- ``symbolic_consistency_check(plan, ...)`` — pairwise floor-implies-
  ceiling across the whole approved plan, returning the unsat core
  when atoms are jointly inconsistent. Catches the failure mode
  where the LLM iterates forever on a satisfiable-looking but
  actually contradictory spec.

- ``generate_atom_traceback(plan, candidate_path, ...)`` — for each
  approved atom, identifies which candidate clauses discharge it and
  surfaces ``⚠`` flags per §6.3 (silent-divergence conditions).
"""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from autocedar.atoms import PropertyAtom, VerificationPlanDraft
from autocedar.grounding import (
    _ceiling_or_floor,
    _is_symcc_tool_error,
    _principal_resource,
    _run_symcc,
)


# ---------------------------------------------------------------------------
# Stage 1.75 — pre-Stage-3 unsat detection.
# ---------------------------------------------------------------------------

@dataclass
class ConsistencyResult:
    """Output of ``symbolic_consistency_check``."""

    unsat: bool
    core: list[str] = field(default_factory=list)
    detail: str = ""
    tool_error: bool = False


def symbolic_consistency_check(
    plan: VerificationPlanDraft,
    schema_path: str,
    workdir: Optional[Path] = None,
) -> ConsistencyResult:
    """Verify the approved plan is jointly satisfiable.

    Pairwise check: for every (floor, ceiling) pair on the same action,
    ``cedar symcc implies floor⊆ceiling`` must hold. If any pair fails,
    those two atoms form the unsat core. Multiple failures return all
    involved atoms as the core.
    """
    workdir = workdir or Path(tempfile.mkdtemp(prefix="autocedar_consistency_"))
    workdir.mkdir(parents=True, exist_ok=True)

    failed_pairs: list[tuple[str, str, str]] = []

    # Group atoms by action for efficiency.
    by_action: dict[str, list[PropertyAtom]] = {}
    for atom in plan.properties:
        by_action.setdefault(atom.action, []).append(atom)

    for action, atoms in by_action.items():
        floors = [a for a in atoms if _ceiling_or_floor(a) == "floor"]
        ceilings = [a for a in atoms if _ceiling_or_floor(a) == "ceiling"]
        if not (floors and ceilings):
            continue

        # Need a representative atom for principal/resource type lookup.
        rep = floors[0] if floors else ceilings[0]
        try:
            principal_type, resource_type = _principal_resource(rep)
        except ValueError as e:
            return ConsistencyResult(
                unsat=True,
                core=[],
                detail=f"plan misconfigured: {e}",
            )

        for floor in floors:
            for ceiling in ceilings:
                floor_path = workdir / f"{floor.name}_floor.cedar"
                ceiling_path = workdir / f"{ceiling.name}_ceiling.cedar"
                floor_path.write_text(floor.reference_cedar)
                ceiling_path.write_text(ceiling.reference_cedar)

                passed, output = _run_symcc(
                    schema_path,
                    principal_type,
                    action,
                    resource_type,
                    "implies",
                    ["--policies1", str(floor_path), "--policies2", str(ceiling_path)],
                )
                if _is_symcc_tool_error(output):
                    return ConsistencyResult(
                        unsat=False,
                        detail=output,
                        tool_error=True,
                    )
                if not passed:
                    failed_pairs.append((floor.name, ceiling.name, output[:200]))

    if not failed_pairs:
        return ConsistencyResult(unsat=False)

    core = sorted({n for pair in failed_pairs for n in pair[:2]})
    detail = "; ".join(
        f"{floor} not contained in {ceiling}" for floor, ceiling, _ in failed_pairs
    )
    return ConsistencyResult(unsat=True, core=core, detail=detail)


# ---------------------------------------------------------------------------
# Stage 2.5 — atom-to-policy traceback.
# ---------------------------------------------------------------------------

@dataclass
class TracebackEntry:
    """Per-atom Stage 2.5 traceback for UI display.

    ``clauses`` is the candidate-policy clauses (raw text) that the
    Stage 2.5 routine identifies as relevant to discharging this atom.
    ``flags`` lists the §6.3 silent-divergence conditions that fire
    on this atom's traceback.
    """

    atom_name: str
    clauses: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


# Cedar attribute reference: dotted access on `principal`, `resource`,
# `context`. Captures the attribute path so we can compare against
# what the atom mentioned. Best-effort; no full Cedar parse.
_ATTR_RE = re.compile(
    r"\b(?:principal|resource|context)\.[A-Za-z_][A-Za-z0-9_]*"
    r"(?:\.[A-Za-z_][A-Za-z0-9_]*)*",
)


def _extract_attribute_paths(text: str) -> set[str]:
    """Pull dotted-attribute references (best-effort) from Cedar text."""
    return set(_ATTR_RE.findall(text))


def _split_clauses(candidate_text: str) -> list[str]:
    """Split a Cedar policy text into top-level permit/forbid clauses.

    Best-effort splitter that respects brace balance — a single permit
    or forbid statement is a contiguous block ending with ``;`` at
    depth 0. Comments and whitespace between clauses are dropped.
    """
    out: list[str] = []
    buf: list[str] = []
    depth = 0
    i = 0
    n = len(candidate_text)
    while i < n:
        ch = candidate_text[i]
        buf.append(ch)
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == ";" and depth == 0:
            clause = "".join(buf).strip()
            if clause and ("permit" in clause or "forbid" in clause):
                out.append(clause)
            buf = []
        i += 1
    # Trailing content (no semicolon) is ignored.
    return out


_CEDAR_IDIOMS = ("permit", "forbid", "when", "unless", "in", "is", "has", "like")


def _idioms_used(text: str) -> set[str]:
    """Best-effort: which Cedar control idioms appear in this text."""
    out: set[str] = set()
    for idiom in _CEDAR_IDIOMS:
        if re.search(rf"\b{idiom}\b", text):
            out.add(idiom)
    return out


def _atom_action_matches_clause(clause: str, action: str) -> bool:
    """Heuristic: does this clause apply to ``action``?"""
    action_literal = action if action.startswith("Action::") else f'Action::"{action}"'
    return action_literal in clause or f'"{action}"' in clause


def _compute_traceback_for_atom(
    atom: PropertyAtom, candidate_clauses: list[str],
) -> TracebackEntry:
    """Identify clauses relevant to the atom and compute §6.3 flags."""
    if atom.constraint_type == "liveness":
        # Liveness atoms are not discharged by specific clauses; they
        # require any-permit on the action. The traceback is just the
        # set of permit clauses on the same action.
        relevant = [
            c for c in candidate_clauses
            if c.lstrip().startswith("permit") and _atom_action_matches_clause(c, atom.action)
        ]
        return TracebackEntry(atom_name=atom.name, clauses=relevant, flags=[])

    relevant = [c for c in candidate_clauses if _atom_action_matches_clause(c, atom.action)]
    flags: list[str] = []

    # §6.3 flag 1: candidate references attributes not in atom's source excerpt.
    candidate_attrs = set()
    for c in relevant:
        candidate_attrs |= _extract_attribute_paths(c)
    excerpt_attrs = _extract_attribute_paths(atom.source_excerpt) | _extract_attribute_paths(
        atom.plain_english_summary,
    ) | _extract_attribute_paths(atom.reference_cedar)
    novel_attrs = candidate_attrs - excerpt_attrs
    if novel_attrs:
        flags.append(
            "uses-attribute-not-in-atom-prose: " + ", ".join(sorted(novel_attrs)),
        )

    # §6.3 flag 2: multi-clause interaction.
    if len(relevant) > 1:
        flags.append("multi-clause-interaction")

    # §6.3 flag 3: encoding uses Cedar idiom absent from atom encoding.
    atom_idioms = _idioms_used(atom.reference_cedar)
    candidate_idioms: set[str] = set()
    for c in relevant:
        candidate_idioms |= _idioms_used(c)
    novel_idioms = (candidate_idioms - atom_idioms) - {"permit", "forbid", "when"}
    if novel_idioms:
        flags.append("idiom-not-in-atom-encoding: " + ", ".join(sorted(novel_idioms)))

    return TracebackEntry(atom_name=atom.name, clauses=relevant, flags=flags)


def generate_atom_traceback(
    plan: VerificationPlanDraft,
    candidate_path: str,
    schema_path: Optional[str] = None,
) -> list[TracebackEntry]:
    """Stage 2.5 — atom-to-policy traceback.

    For each atom in the plan, identify the candidate clauses relevant
    to discharging it and surface §6.3 silent-divergence flags. Mutates
    each atom's ``traceback_clauses`` and ``traceback_flags`` in place
    so corpus logging captures the result.

    ``schema_path`` is reserved for a future ``cedar symcc``-driven
    minimum-sufficient-subset search. Current behavior uses a conservative
    string-based traceback over candidate clauses.
    """
    candidate_text = Path(candidate_path).read_text()
    clauses = _split_clauses(candidate_text)

    out: list[TracebackEntry] = []
    for atom in plan.properties:
        entry = _compute_traceback_for_atom(atom, clauses)
        atom.traceback_clauses = entry.clauses
        atom.traceback_flags = entry.flags
        out.append(entry)
    return out
