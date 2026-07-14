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
import re
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
    lines.extend(_edit_hint_lines(atom))
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


def render_property_atom(atom: PropertyAtom, index: int, total: int | None) -> str:
    """Render a property atom for terminal review (Stage 2 — §6.1)."""
    lines: list[str] = []
    progress = f"[Property {index} of {total}]" if total else f"[Property {index}]"
    kind = (
        "LIVENESS CHECK (not schema)"
        if atom.constraint_type == "liveness"
        else atom.constraint_type.upper()
    )
    lines.append(
        f"{progress}  {kind} — "
        f"{_review_summary(atom)}",
    )
    lines.append("")
    lines.append(f"  Source excerpt: {atom.source_excerpt!r}")
    lines.append("")
    if atom.constraint_type == "liveness":
        lines.append(
            "  This is a verifier liveness check, not schema text. It asks whether "
            "the final policy permits at least one matching request.",
        )
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
        for line in format_symbolic_verification_log(atom.symbolic_verification_log):
            lines.append(f"    {line}")
    lines.append("")
    lines.extend(_edit_hint_lines(atom))
    lines.append("")
    lines.append("  [A]pprove  [R]eject  [E]dit  [Q]uestion  [S]ee Cedar")
    return "\n".join(lines)


def _review_summary(atom: PropertyAtom) -> str:
    if atom.constraint_type != "liveness":
        return atom.plain_english_summary
    summary = atom.plain_english_summary.strip()
    lowered = summary.lower()
    prefix = "there exists a permitted request in which "
    if lowered.startswith(prefix):
        rest = summary[len(prefix):].strip()
        return f"At least one request should be permitted where {rest}"
    if lowered.startswith("there exists a permitted request"):
        return summary.replace("There exists a permitted request", "At least one request should be permitted", 1)
    return summary


def _edit_hint_lines(atom: ReviewableAtom) -> list[str]:
    """Short edit examples shown in the review card."""
    examples: list[str]
    if isinstance(atom, AttributeAtom):
        examples = [
            "E cedar_type=Bool",
            "E optional=true",
            "E field_name=isPublic",
        ]
    elif isinstance(atom, EntityAtom):
        examples = ["E name=Document", "E plain_english_summary=..."]
    elif isinstance(atom, ActionAtom):
        examples = [
            "E principal_types=User,Admin",
            "E resource_types=Document",
        ]
    elif isinstance(atom, TypeAliasAtom):
        examples = ["E cedar_type={ owner: User, isPublic: Bool }"]
    elif isinstance(atom, PropertyAtom):
        examples = [
            "E constraint_type=floor",
            "E principal_types=User",
            "E reference_cedar=permit (...) when { ... };",
        ]
    else:
        examples = ["E plain_english_summary=..."]
    return [
        "  Edit examples:",
        "    " + " | ".join(examples),
    ]


def render_property_reference(atom: PropertyAtom) -> str:
    """Render the review-time Cedar or explanation for a property atom.

    Most ceiling/floor/sugar atoms have a reference Cedar policy. Liveness
    atoms deliberately do not: they assert that some request must be allowed
    and are checked through the generated verification plan.
    """
    if atom.reference_cedar.strip():
        return atom.reference_cedar.strip()
    if atom.constraint_type == "liveness":
        return "\n".join(
            [
                "// Liveness property: no standalone reference policy.",
                "// AutoCedar checks this by asking Cedar symcc whether the",
                "// synthesized policy always denies this action/resource shape.",
                f"// Action: {atom.action}",
                f"// Principal types: {', '.join(atom.principal_types) or '(none)'}",
                f"// Resource types: {', '.join(atom.resource_types) or '(none)'}",
                f"// Intent: {atom.plain_english_summary}",
            ],
        )
    return "\n".join(
        [
            "// No reference Cedar was attached to this property atom.",
            f"// Constraint type: {atom.constraint_type}",
            f"// Intent: {atom.plain_english_summary}",
        ],
    )


def format_symbolic_verification_log(log: list[str]) -> list[str]:
    """Translate internal verifier labels into user-facing review notes."""
    parsed = [_parse_symbolic_log_line(line) for line in log]
    has_failure = any(status == "FAILED" for _, status, _ in parsed)
    out: list[str] = []

    for name, status, detail in parsed:
        if not status:
            out.append(name)
            continue
        if name == "sugar-universal" and status == "ok" and (
            not detail or "not applicable" in detail.lower()
        ):
            continue
        if name == "type-correct":
            if status == "ok":
                if detail and detail != "n/a" and has_failure:
                    out.append(f"Schema/type check: OK ({detail}).")
                elif has_failure:
                    out.append("Schema/type check: OK.")
                elif detail == "n/a":
                    out.append("Schema/type check: skipped; liveness has no Cedar body.")
                else:
                    out.append("Schema/type check: OK.")
            else:
                out.append(_type_error_message(detail))
            continue
        if name == "satisfiable":
            if status == "ok":
                if detail and "liveness atom" in detail.lower():
                    out.append(
                        "Liveness check: records that at least one matching request "
                        "should be permitted.",
                    )
                elif has_failure:
                    out.append(
                        "Satisfiability check: OK; the property is not contradictory. "
                        "This does not override the failed check above.",
                    )
                else:
                    out.append(
                        "Satisfiability check: OK; the property is not vacuous.",
                    )
            else:
                out.append(
                    "Satisfiability check failed: this encoding appears vacuous "
                    "or contradictory. Reject or edit it before approving."
                    + (f" Details: {_compact_detail(detail)}" if detail else ""),
                )
            continue
        if name.startswith("joint-consistency"):
            label = name.removeprefix("joint-consistency-with-")
            if status == "ok":
                if has_failure:
                    out.append(f"Consistency with `{label}`: OK.")
            else:
                out.extend(_consistency_error_lines(label, detail))
            continue
        if name == "sugar-universal":
            if status == "ok":
                if "not applicable" not in detail.lower():
                    out.append("Sugar encoding check: OK.")
            else:
                out.append(
                    "Sugar encoding check failed: "
                    f"{_compact_detail(detail) or 'the compiled sugar form is incomplete.'}",
                )
            continue
        out.append(
            f"{name}: {'OK' if status == 'ok' else 'failed'}"
            + (f" — {_compact_detail(detail)}" if detail else ""),
        )

    return out


def _parse_symbolic_log_line(line: str) -> tuple[str, str, str]:
    name, sep, rest = line.partition(":")
    if not sep:
        return line, "", ""
    rest = rest.strip()
    status = "ok" if rest.startswith("ok") else "FAILED" if rest.startswith("FAILED") else ""
    detail = ""
    match = re.search(r"\((.*)\)\s*$", rest, flags=re.DOTALL)
    if match:
        detail = match.group(1).strip()
    return name.strip(), status, detail


def _type_error_message(detail: str) -> str:
    unresolved = re.search(r"failed to resolve type:\s*([A-Za-z_][A-Za-z0-9_]*)", detail)
    if unresolved:
        return (
            "Schema/type check failed: this property mentions "
            f"`{unresolved.group(1)}`, but the approved schema does not define "
            f"`{unresolved.group(1)}` as an entity/type. Reject or edit this atom "
            "before approving."
        )
    return (
        "Schema/type check failed: Cedar rejected this property against the current "
        "schema. Reject or edit this atom before approving."
        + (f" Details: {_compact_detail(detail)}" if detail else "")
    )


def _compact_detail(detail: str, limit: int = 260) -> str:
    compacted = " ".join(detail.split())
    if len(compacted) <= limit:
        return compacted
    return compacted[: limit - 3].rstrip() + "..."


def _consistency_error_lines(label: str, detail: str) -> list[str]:
    parsed = _parse_consistency_detail(detail)
    if parsed is None:
        return [
            f"Consistency check failed against `{label}`: "
            f"{_compact_detail(detail) or 'the floor and ceiling conflict.'}",
        ]
    summary, floor_ref, ceiling_ref, symcc_output = parsed
    lines = [
        f"Consistency check failed against `{label}`: {summary}",
        "Compared floor reference:",
        _indent_block(floor_ref),
        "Compared ceiling reference:",
        _indent_block(ceiling_ref),
    ]
    if symcc_output:
        if _is_symcc_setup_error(symcc_output):
            lines.extend([
                "Cedar verifier setup error:",
                _indent_block(_compact_detail(symcc_output, limit=520)),
            ])
            return lines
        lines.extend([
            "Cedar counterexample summary:",
            _indent_block(_compact_detail(symcc_output, limit=420)),
        ])
    return lines


def _parse_consistency_detail(detail: str) -> tuple[str, str, str, str] | None:
    floor_marker = "\nFloor reference:\n"
    ceiling_marker = "\nCeiling reference:\n"
    symcc_marker = "\nCedar symcc output:\n"
    if floor_marker not in detail or ceiling_marker not in detail:
        return None
    summary, rest = detail.split(floor_marker, 1)
    floor_ref, rest = rest.split(ceiling_marker, 1)
    if symcc_marker in rest:
        ceiling_ref, symcc_output = rest.split(symcc_marker, 1)
    else:
        ceiling_ref, symcc_output = rest, ""
    return (
        summary.strip() or "the floor and ceiling conflict.",
        floor_ref.strip(),
        ceiling_ref.strip(),
        symcc_output.strip(),
    )


def _indent_block(text: str) -> str:
    return "\n".join(f"      {line}" for line in text.splitlines())


def _is_symcc_setup_error(text: str) -> bool:
    return (
        "Cedar symcc setup error:" in text
        or "not built with `analyze` experimental feature enabled" in text
        or "not built with the `analyze` feature enabled" in text
        or "unexpected argument '--principal-type'" in text
        or "unexpected argument '--resource-type'" in text
        or "unexpected argument '--action'" in text
    )


# ---------------------------------------------------------------------------
# Auto-approve reviewer (non-interactive, used by tests and batch eval).
# ---------------------------------------------------------------------------


def auto_approve(atom: Any) -> AtomDecision:
    """Non-interactive reviewer for batch runs.

    This is still only a plumbing convenience; it is not semantic HITL
    validation, so an approval returned here deliberately leaves
    ``intent_acknowledged_by_user`` false. It must also not approve a property
    atom whose verifier checks failed, because that would let invalid reference
    Cedar enter the formal target and later fail as a plan-level tooling error.
    """
    if isinstance(atom, PropertyAtom) and not getattr(atom, "symbolic_verified", False):
        log = getattr(atom, "symbolic_verification_log", []) or []
        reason = "Symbolic verification failed; auto-approve refuses invalid property atoms."
        if log:
            reason += " " + str(log[0])
        return AtomDecision(
            atom_name=getattr(atom, "name", "?"),
            action="reject",
            reason=reason,
            intent_acknowledged_by_user=False,
            symbolic_verified=False,
        )
    return AtomDecision(
        atom_name=getattr(atom, "name", "?"),
        action="approve",
        intent_acknowledged_by_user=False,
        symbolic_verified=getattr(atom, "symbolic_verified", False),
    )


# ---------------------------------------------------------------------------
# Interactive review loop.
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
      [R]eject     prompt for reason. Stage 1 schema review asks the LLM
                   for an alternative when available. Stage 2 property
                   repair is handled by the authoring pipeline.
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
    force_approve_failed_property = False

    while True:
        output_fn(_render_review_atom(current, index, total))
        key = (input_fn("> ") or "").strip().upper()[:1]

        if key == "A":
            if _approval_needs_failed_property_confirmation(
                current,
                force_approve_failed_property,
            ):
                output_fn(
                    "Symbolic checks failed for this property. "
                    "Edit or reject it, or press A again to force approval.",
                )
                force_approve_failed_property = True
                continue
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
                force_approve_failed_property = False
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
                output_fn(render_property_reference(current))
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
        force_approve_failed_property = False


def _approval_needs_failed_property_confirmation(
    atom: ReviewableAtom,
    already_confirmed: bool,
) -> bool:
    if already_confirmed or not isinstance(atom, PropertyAtom):
        return False
    if atom.symbolic_verified:
        return False
    return any("FAILED" in line for line in atom.symbolic_verification_log)


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
      ``resource_types`` (comma-separated), and context attributes with
      ``context.field=Type`` or optional ``context.field?=Type``.
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
    target_field = field_name
    old_value: Any = getattr(atom, field_name, None)
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
    elif field_name.startswith("context.") and isinstance(atom, ActionAtom):
        context_name = field_name[len("context."):].strip()
        optional = False
        if context_name.endswith("?"):
            optional = True
            context_name = context_name[:-1].strip()
        if not context_name:
            raise ValueError("context edit expects `context.field=Type`")
        target_field = "context_attributes"
        old_value = dict(atom.context_attributes)
        updated_context = dict(atom.context_attributes)
        if value.lower() in {"", "none", "remove", "delete"}:
            updated_context.pop(context_name, None)
        else:
            updated_context[context_name] = AttributeAtom(
                name=f"{atom.name}__context__{context_name}",
                rationale=f"context attribute on action {atom.name}",
                plain_english_summary=(
                    f"The {atom.name} request carries context.{context_name}."
                ),
                source_excerpt=atom.source_excerpt,
                on_entity="",
                field_name=context_name,
                cedar_type=value,
                optional=optional,
            )
        new_value = updated_context
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

    updated = dataclasses.replace(atom, **{target_field: new_value})
    if isinstance(updated, PropertyAtom):
        updated.symbolic_verified = False
        updated.symbolic_verification_log = [
            "edited after symbolic verification; checks will be rerun after approval",
        ]
    edit_log.setdefault("edits", []).append(
        {"field": field_name, "old": old_value, "new": new_value},
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
