"""Terminal review UI for atom approval.

See ``docs/HITL_STEP_B_PLAN.md`` §6 for the UI contract (verified-badge
text, key dispatch) and ``docs/HITL_STEP_C_PLAN.md`` §3 (acceptance
criterion 4) for the interactive review loop:

- Handles all six keys: ``[A]pprove`` / ``[R]eject`` / ``[E]dit`` /
  ``[Q]uestion`` / ``[S]ee Cedar`` / ``[V]iew patches``.
- Accepts injected ``input_fn`` / ``output_fn`` so tests script user
  input without touching stdin/stdout.
- Returns ``ReviewedAtom`` records: the (possibly edited or replaced)
  atom paired with an ``AtomDecision`` for the corpus.

Per HITL_STEP_B_PLAN §1.4, the verified-badge text is:

    ✓ Formally consistent — does this match your intent?

and the user's approval sets ``intent_acknowledged_by_user=True``,
independent of the symcc-driven ``symbolic_verified`` flag.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, Callable, Optional, Union

from autocedar.atoms import (
    ActionAtom,
    AttributeAtom,
    EntityAtom,
    PropertyAtom,
    TypeAliasAtom,
)
from autocedar.corpus import AtomDecision
from autocedar.llm import LLMClient, Stage1Atom

VERIFIED_BADGE = "✓ Formally consistent — does this match your intent?"
UNVERIFIED_BADGE = "✗ Symbolic checks failed — review carefully before approving"
ReviewableAtom = Union[Stage1Atom, PropertyAtom]


# ---------------------------------------------------------------------------
# Result types.
# ---------------------------------------------------------------------------


@dataclass
class ReviewedAtom:
    """One atom plus the user's decision on it.

    The ``atom`` field reflects any edits the user made via ``[E]`` or
    any LLM-proposed replacements after ``[R]``. The pipeline composes
    the final draft from these post-review atoms.
    """

    atom: ReviewableAtom
    decision: AtomDecision


# ---------------------------------------------------------------------------
# Atom rendering.
# ---------------------------------------------------------------------------


def render_schema_atom(atom: Stage1Atom, index: int, total: int) -> str:
    """Render a Stage 1 atom for terminal review.

    The verified-badge line on Stage 1 atoms reflects only structural
    validation (``cedar validate`` will run after composition);
    symbolic verification (§4 of HITL_STEP_B_PLAN.md) applies only to
    Stage 2 property atoms.
    """
    kind = _atom_kind_label(atom)
    lines = [f"[Atom {index} of {total}]  {kind}: {atom.name}", ""]
    lines.append(f"  {atom.plain_english_summary}")
    lines.append("")
    lines.append(f"  Source excerpt: {atom.source_excerpt!r}")
    lines.append(f"  Rationale: {atom.rationale}")

    if isinstance(atom, EntityAtom):
        if atom.members_of:
            lines.append(f"  Members of: {', '.join(atom.members_of)}")
        if atom.enum_values is not None:
            values = ", ".join(f'"{v}"' for v in atom.enum_values)
            lines.append(f"  Enum values: [{values}]")
    elif isinstance(atom, AttributeAtom):
        on_label = atom.on_entity if atom.on_entity else "(context)"
        lines.append(f"  On entity: {on_label}")
        lines.append(f"  Field: {atom.field_name}: {atom.cedar_type}"
                     + ("?" if atom.optional else ""))
        if atom.alternatives_considered:
            lines.append("  Alternatives considered:")
            for alt in atom.alternatives_considered:
                lines.append(f"    - {alt}")
    elif isinstance(atom, ActionAtom):
        lines.append(
            f"  Principal types: [{', '.join(atom.principal_types)}]",
        )
        lines.append(
            f"  Resource types:  [{', '.join(atom.resource_types)}]",
        )
        if atom.context_attributes:
            lines.append("  Context:")
            for name, ctx in atom.context_attributes.items():
                lines.append(
                    f"    - {name}: {ctx.cedar_type}"
                    + ("?" if ctx.optional else ""),
                )
        if atom.parent_groups:
            lines.append(f"  Parent groups: {', '.join(atom.parent_groups)}")
    elif isinstance(atom, TypeAliasAtom):
        lines.append(f"  Cedar type: {atom.cedar_type}")

    lines.append("")
    lines.append("  [A]pprove  [R]eject  [E]dit  [Q]uestion  [S]ee Cedar  [V]iew patches")
    return "\n".join(lines)


def render_schema_declaration(atom: Stage1Atom) -> str:
    """Render the Cedar text that would be emitted for this atom alone.

    Used by the ``[S]`` key in the review loop. For attributes, shows
    a stub entity context so the line is readable on its own.
    """
    if isinstance(atom, EntityAtom):
        if atom.enum_values is not None:
            values = ", ".join(f'"{v}"' for v in atom.enum_values)
            return f"entity {atom.name} enum [{values}];"
        if atom.members_of:
            parents = ", ".join(atom.members_of)
            return f"entity {atom.name} in [{parents}] {{ ... }};"
        return f"entity {atom.name} {{ ... }};"
    if isinstance(atom, AttributeAtom):
        marker = "?" if atom.optional else ""
        owner = atom.on_entity if atom.on_entity else "<context>"
        return f"// on entity {owner}\n{atom.field_name}{marker}: {atom.cedar_type},"
    if isinstance(atom, ActionAtom):
        principals = ", ".join(atom.principal_types) or "..."
        resources = ", ".join(atom.resource_types) or "..."
        ctx_lines = []
        for name, ctx in atom.context_attributes.items():
            marker = "?" if ctx.optional else ""
            ctx_lines.append(f"        {name}{marker}: {ctx.cedar_type},")
        ctx_block = (
            "    context: {\n" + "\n".join(ctx_lines) + "\n    },"
            if ctx_lines else ""
        )
        return (
            f"action {atom.name} appliesTo {{\n"
            f"    principal: [{principals}],\n"
            f"    resource: [{resources}],"
            + (f"\n{ctx_block}" if ctx_block else "")
            + "\n};"
        )
    if isinstance(atom, TypeAliasAtom):
        return f"type {atom.name} = {atom.cedar_type};"
    return f"// unknown atom kind: {type(atom).__name__}"


def render_property_atom(atom: PropertyAtom, index: int, total: int) -> str:
    """Render a property atom for terminal review (Stage 2 — §6.1)."""
    lines: list[str] = []
    lines.append(
        f"[Property {index} of {total}]  {atom.constraint_type.upper()} — "
        f"{atom.plain_english_summary}",
    )
    lines.append("")
    lines.append(f"  Source excerpt: {atom.source_excerpt!r}")
    lines.append("")
    if atom.examples_adversarial:
        lines.append("  Adversarial examples (probing the boundary with plausible alternatives):")
        for ex in atom.examples_adversarial:
            lines.append(f"    {ex.description}")
            lines.append(f"      chosen encoding: {ex.decision_under_chosen}")
            for label, dec in ex.decisions_under_alternatives.items():
                lines.append(f"      alternative '{label}': {dec}")
        lines.append("")
    badge = VERIFIED_BADGE if atom.symbolic_verified else UNVERIFIED_BADGE
    lines.append(f"  {badge}")
    if atom.symbolic_verification_log:
        log_summary = "; ".join(atom.symbolic_verification_log[:3])
        lines.append(f"    [{log_summary}]")
    lines.append("")
    lines.append("  [A]pprove  [R]eject  [E]dit  [Q]uestion  [S]ee Cedar")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Auto-approve reviewer (non-interactive, used by tests and batch eval).
# ---------------------------------------------------------------------------


def auto_approve(atom: Any) -> AtomDecision:
    """Non-interactive reviewer: approve everything and mark intent ack."""
    return AtomDecision(
        atom_name=getattr(atom, "name", "?"),
        action="approve",
        intent_acknowledged_by_user=True,
        symbolic_verified=getattr(atom, "symbolic_verified", False),
    )


# ---------------------------------------------------------------------------
# Interactive review loop — Step C acceptance criterion 4.
# ---------------------------------------------------------------------------


InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]


def interactive_review_loop(
    atoms: list[ReviewableAtom],
    *,
    llm: Optional[LLMClient] = None,
    spec_text: str = "",
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
) -> list[ReviewedAtom]:
    """Walk the user through each atom one at a time.

    Dispatches on six keys per HITL_STEP_B_PLAN.md §6.2:

      [A]pprove    advance to next atom
      [R]eject     prompt for reason; if LLM available, ask for an
                   alternative atom and re-present; otherwise record
                   the rejection and move on.
      [E]dit       prompt for a ``field=value`` line; update the atom
                   via dataclasses.replace and re-present.
      [Q]uestion   prompt for free-text question; if LLM available,
                   surface the answer; otherwise record the question
                   and stay on the same atom.
      [S]ee Cedar  print the Cedar declaration for this atom and stay
                   on the same atom.
      [V]iew patches  Stage 1 has no patches; print a note and stay
                   on the same atom.

    Returns one ``ReviewedAtom`` per input atom in the same order. The
    ``atom`` field may differ from the input (edits / replacements).
    """
    results: list[ReviewedAtom] = []
    for i, atom in enumerate(atoms):
        reviewed = _review_one_atom(
            atom,
            index=i + 1,
            total=len(atoms),
            llm=llm,
            spec_text=spec_text,
            input_fn=input_fn,
            output_fn=output_fn,
        )
        results.append(reviewed)
    return results


def _review_one_atom(
    atom: ReviewableAtom,
    *,
    index: int,
    total: int,
    llm: Optional[LLMClient],
    spec_text: str,
    input_fn: InputFn,
    output_fn: OutputFn,
) -> ReviewedAtom:
    """Per-atom review loop. See ``interactive_review_loop`` for the contract."""
    current = atom
    edit_log: dict[str, Any] = {}

    while True:
        output_fn(_render_review_atom(current, index, total))
        key = (input_fn("> ") or "").strip().upper()[:1]

        if key == "A":
            return ReviewedAtom(
                atom=current,
                decision=AtomDecision(
                    atom_name=current.name,
                    action="approve",
                    intent_acknowledged_by_user=True,
                    symbolic_verified=getattr(current, "symbolic_verified", False),
                    edit_delta=edit_log,
                ),
            )
        if key == "R":
            reason = (input_fn("Reason: ") or "").strip()
            if llm is None or isinstance(current, PropertyAtom):
                return ReviewedAtom(
                    atom=current,
                    decision=AtomDecision(
                        atom_name=current.name,
                        action="reject",
                        reason=reason,
                        edit_delta=edit_log,
                    ),
                )
            output_fn("(asking the agent for an alternative...)")
            replacement = llm.propose_alternative_atom(current, reason, spec_text)
            if replacement is None:
                output_fn("(the agent did not propose an alternative; "
                          "atom recorded as rejected)")
                return ReviewedAtom(
                    atom=current,
                    decision=AtomDecision(
                        atom_name=current.name,
                        action="reject",
                        reason=reason,
                        edit_delta=edit_log,
                    ),
                )
            current = replacement
            edit_log["reject_reason"] = reason
            edit_log["replaced_by_llm"] = True
            continue
        if key == "E":
            edit_input = (input_fn("Edit (field=value): ") or "").strip()
            try:
                current = _apply_field_edit(current, edit_input, edit_log)
                output_fn("(atom updated; re-presenting)")
            except ValueError as e:
                output_fn(f"(edit rejected: {e}; atom unchanged)")
            continue
        if key == "Q":
            question = (input_fn("Q: ") or "").strip()
            edit_log.setdefault("questions", []).append(question)
            if llm is None:
                output_fn("(no LLM connected; question recorded — "
                          "approve / reject / edit when ready)")
                continue
            answer = llm.answer_question_about_atom(current, question, spec_text)
            output_fn(f"Agent: {answer}")
            continue
        if key == "S":
            if isinstance(current, PropertyAtom):
                output_fn("```cedar")
                output_fn(current.reference_cedar or "// liveness property has no reference policy")
                output_fn("```")
            else:
                output_fn("```cedarschema")
                output_fn(render_schema_declaration(current))
                output_fn("```")
            continue
        if key == "V":
            if isinstance(current, PropertyAtom):
                logs = current.symbolic_verification_log or ["no symbolic log recorded"]
                output_fn("\n".join(logs))
            else:
                output_fn(
                    "(no §8.8 patches or schema amendments apply to a Stage 1 atom)",
                )
            continue
        # Unknown key.
        output_fn(f"unknown key {key!r}; valid: A / R / E / Q / S / V")


def _render_review_atom(atom: ReviewableAtom, index: int, total: int) -> str:
    if isinstance(atom, PropertyAtom):
        return render_property_atom(atom, index, total)
    return render_schema_atom(atom, index, total)


# ---------------------------------------------------------------------------
# Edit support — field=value path.
# ---------------------------------------------------------------------------


def _apply_field_edit(
    atom: ReviewableAtom, edit_input: str, edit_log: dict[str, Any],
) -> ReviewableAtom:
    """Apply a ``field=value`` edit to a Stage 1 atom.

    Supported fields per atom kind:

    - All atoms: ``name``, ``rationale``, ``plain_english_summary``,
      ``source_excerpt``.
    - AttributeAtom: ``on_entity``, ``field_name``, ``cedar_type``,
      ``optional`` (``true``/``false``).
    - ActionAtom: ``principal_types`` (comma-separated),
      ``resource_types`` (comma-separated).
    - TypeAliasAtom: ``cedar_type``.

    For more complex edits (adding context attributes, editing
    alternatives_considered), the user rejects and lets the LLM
    propose a replacement.
    """
    if "=" not in edit_input:
        raise ValueError("expected `field=value`")
    field_name, value = edit_input.split("=", 1)
    field_name = field_name.strip()
    value = value.strip()

    if not field_name:
        raise ValueError("empty field name")

    common_fields = {"name", "rationale", "plain_english_summary", "source_excerpt"}

    new_value: Any
    if field_name in common_fields:
        new_value = value
    elif field_name == "optional" and isinstance(atom, AttributeAtom):
        if value.lower() not in ("true", "false"):
            raise ValueError(f"optional expects true/false; got {value!r}")
        new_value = value.lower() == "true"
    elif field_name in ("on_entity", "field_name", "cedar_type") and isinstance(atom, AttributeAtom):
        new_value = value
    elif field_name in ("principal_types", "resource_types") and isinstance(atom, ActionAtom):
        new_value = [t.strip() for t in value.split(",") if t.strip()]
    elif field_name == "cedar_type" and isinstance(atom, TypeAliasAtom):
        new_value = value
    elif field_name == "constraint_type" and isinstance(atom, PropertyAtom):
        new_value = value
    elif field_name == "action" and isinstance(atom, PropertyAtom):
        new_value = value
    elif field_name in ("principal_types", "resource_types") and isinstance(atom, PropertyAtom):
        new_value = [t.strip() for t in value.split(",") if t.strip()]
    elif field_name == "reference_cedar" and isinstance(atom, PropertyAtom):
        new_value = value
    elif field_name in {
        "rate_limit_window",
        "rate_limit_counter_attr",
        "disjoint_with",
        "disjoint_target_body",
    } and isinstance(atom, PropertyAtom):
        new_value = value
    elif field_name == "rate_limit_threshold" and isinstance(atom, PropertyAtom):
        try:
            new_value = int(value)
        except ValueError as exc:
            raise ValueError("rate_limit_threshold expects an integer") from exc
    else:
        raise ValueError(
            f"field {field_name!r} is not editable on {type(atom).__name__}",
        )

    updated = dataclasses.replace(atom, **{field_name: new_value})
    edit_log.setdefault("edits", []).append(
        {"field": field_name, "old": getattr(atom, field_name), "new": new_value},
    )
    return updated


def _atom_kind_label(atom: Stage1Atom) -> str:
    """Short human-readable label for the atom kind."""
    if isinstance(atom, EntityAtom):
        return "ENTITY"
    if isinstance(atom, AttributeAtom):
        return "ATTRIBUTE"
    if isinstance(atom, ActionAtom):
        return "ACTION"
    if isinstance(atom, TypeAliasAtom):
        return "TYPE_ALIAS"
    return type(atom).__name__.upper()
