"""LLM wrapper for autocedar.

See ``docs/HITL_STEP_C_PLAN.md`` for the implementation contract.
Per §2 of that plan:

- Default provider is the local Codex OAuth bridge. Anthropic remains an
  explicit opt-in provider for deployments that set ``AUTOCEDAR_PROVIDER``.
- Adaptive thinking is on; ``effort`` defaults to ``"high"``.
- The system prompt + the spec text are sent as cache-controlled
  blocks so repeated calls in one session amortize the input-token
  cost. Per-turn user content stays uncached.
- The constructor accepts an optional ``client`` (an
    ``anthropic.Anthropic`` instance, the Codex OAuth adapter, or any
    object with the same ``messages.parse`` shape) so tests inject a mock
    without touching the network. The minimum cacheable prefix on Opus 4.7 is
    4096 tokens — short specs will silently bypass caching, which is fine.

Structured output is provided via Pydantic schemas at this layer; the
schemas are then translated into the existing dataclasses in
``autocedar.atoms`` so the rest of the pipeline (sugar compile-down,
grounding, etc.) stays unchanged.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field

from autocedar.atoms import (
    ActionAtom,
    AlternativeEncoding,
    AttributeAtom,
    EntityAtom,
    Example,
    PropertyAtom,
    RequiredSchemaSupport,
    SchemaSupportKind,
    TypeAliasAtom,
)
from autocedar.codex_auth import DEFAULT_CODEX_MODEL, CodexAuthClient, is_codex_provider


# ---------------------------------------------------------------------------
# Module defaults.
# ---------------------------------------------------------------------------

DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-7"
DEFAULT_MODEL = DEFAULT_CODEX_MODEL
DEFAULT_MAX_TOKENS = 16000
DEFAULT_EFFORT = "high"
DEFAULT_PROVIDER = "codex"


def default_provider() -> str:
    return os.environ.get("AUTOCEDAR_PROVIDER", DEFAULT_PROVIDER).strip().lower()


def default_model_for_provider(provider: str | None = None) -> str:
    resolved = (provider or default_provider()).strip().lower()
    if is_codex_provider(resolved):
        return os.environ.get("AUTOCEDAR_CODEX_MODEL") or DEFAULT_CODEX_MODEL
    return (
        os.environ.get("AUTOCEDAR_MODEL")
        or os.environ.get("AUTOCEDAR_AUTHOR_MODEL")
        or os.environ.get("AUTOCEDAR_CHAT_MODEL")
        or DEFAULT_ANTHROPIC_MODEL
    )


def _load_prompt(name: str) -> str:
    """Load a prompt template from ``autocedar/prompts/<name>``."""
    path = Path(__file__).resolve().parent / "prompts" / name
    return path.read_text()


# ---------------------------------------------------------------------------
# Pydantic schemas for LLM-side structured output.
#
# These are deliberately a separate layer from ``autocedar.atoms``: the
# LLM gets a clean, discriminator-tagged shape; the rest of the pipeline
# keeps the dataclasses with sugar-specific validation in __post_init__.
# Translation lives in ``_translate_*`` helpers further down.
# ---------------------------------------------------------------------------


class _LLMContextAttribute(BaseModel):
    """Context-attribute fragment owned by an ActionAtom."""

    field_name: str
    cedar_type: str
    optional: bool = False
    rationale: str = ""
    plain_english_summary: str = ""


class _LLMEntityAtom(BaseModel):
    kind: Literal["entity"]
    name: str
    rationale: str
    plain_english_summary: str
    source_excerpt: str
    members_of: list[str] = Field(default_factory=list)
    enum_values: Optional[list[str]] = None


class _LLMAttributeAtom(BaseModel):
    kind: Literal["attribute"]
    name: str
    rationale: str
    plain_english_summary: str
    source_excerpt: str
    on_entity: str
    field_name: str
    cedar_type: str
    optional: bool = False
    alternatives_considered: list[str] = Field(default_factory=list)


class _LLMActionAtom(BaseModel):
    kind: Literal["action"]
    name: str
    rationale: str
    plain_english_summary: str
    source_excerpt: str
    principal_types: list[str] = Field(default_factory=list)
    resource_types: list[str] = Field(default_factory=list)
    context_attributes: list[_LLMContextAttribute] = Field(default_factory=list)
    parent_groups: list[str] = Field(default_factory=list)


class _LLMTypeAliasAtom(BaseModel):
    kind: Literal["type_alias"]
    name: str
    rationale: str
    plain_english_summary: str
    source_excerpt: str
    cedar_type: str


_LLMStage1Atom = Annotated[
    Union[_LLMEntityAtom, _LLMAttributeAtom, _LLMActionAtom, _LLMTypeAliasAtom],
    Field(discriminator="kind"),
]


class SchemaAtomsResponse(BaseModel):
    """Top-level structured response for schema atomization."""

    atoms: list[_LLMStage1Atom]


class SchemaFixResponse(BaseModel):
    """Top-level structured response for schema-fix retries."""

    fixed_schema_text: str
    explanation: str


class _LLMExample(BaseModel):
    """Adversarial example attached to a Stage 2 property atom."""

    description: str
    request_dict: dict[str, Any]
    decision_under_chosen: Literal["permit", "deny"]
    decisions_under_alternatives: dict[str, Literal["permit", "deny"]] = Field(
        default_factory=dict,
    )
    diagnostic_for: list[str] = Field(default_factory=list)


class _LLMAlternativeEncoding(BaseModel):
    """Alternative property encoding considered by the model."""

    label: str
    interpretive_choice: str
    cedar_text: str


class _LLMRequiredSchemaSupport(BaseModel):
    """One schema hook required by a Stage 2 property atom."""

    kind: SchemaSupportKind
    name: str = ""
    entity: str = ""
    action: str = ""
    field_name: str = ""
    type_name: str = ""
    reason: str = ""


class _LLMPropertyAtom(BaseModel):
    """LLM-side Stage 2 property atom."""

    name: str
    rationale: str
    plain_english_summary: str
    source_excerpt: str
    constraint_type: Literal["ceiling", "floor", "liveness", "rate_limit", "disjointness"]
    action: str
    principal_types: list[str] = Field(default_factory=list)
    resource_types: list[str] = Field(default_factory=list)
    reference_cedar: str = ""
    required_schema_support: list[_LLMRequiredSchemaSupport] = Field(default_factory=list)
    examples_adversarial: list[_LLMExample] = Field(default_factory=list)
    alternatives_considered: list[_LLMAlternativeEncoding] = Field(default_factory=list)
    rate_limit_window: Optional[str] = None
    rate_limit_threshold: Optional[int] = None
    rate_limit_counter_attr: Optional[str] = None
    disjoint_with: Optional[str] = None
    disjoint_target_body: Optional[str] = None


class PropertyAtomsResponse(BaseModel):
    """Top-level structured response for Stage 2 property elicitation."""

    atoms: list[_LLMPropertyAtom]


class PropertyRejectionPlanResponse(BaseModel):
    """Structured repair action for a rejected property atom."""

    action: Literal[
        "repair_current_property",
        "repair_prior_property",
        "repair_schema",
        "reject_current",
        "ask_user_clarification",
    ]
    target_atom: Optional[str] = None
    reason: str
    repair_instruction: str = ""
    schema_gap_summary: str = ""


# Translated atom types (returned by ``LLMClient.propose_schema_atoms``).
Stage1Atom = Union[EntityAtom, AttributeAtom, ActionAtom, TypeAliasAtom]


# ---------------------------------------------------------------------------
# Translation: Pydantic LLM atoms → autocedar.atoms dataclasses.
# ---------------------------------------------------------------------------


def _translate_entity(llm: _LLMEntityAtom) -> EntityAtom:
    return EntityAtom(
        name=llm.name,
        rationale=llm.rationale,
        plain_english_summary=llm.plain_english_summary,
        source_excerpt=llm.source_excerpt,
        members_of=list(llm.members_of),
        enum_values=list(llm.enum_values) if llm.enum_values is not None else None,
    )


def _translate_attribute(llm: _LLMAttributeAtom) -> AttributeAtom:
    return AttributeAtom(
        name=llm.name,
        rationale=llm.rationale,
        plain_english_summary=llm.plain_english_summary,
        source_excerpt=llm.source_excerpt,
        on_entity=llm.on_entity,
        field_name=llm.field_name,
        cedar_type=llm.cedar_type,
        optional=llm.optional,
        alternatives_considered=list(llm.alternatives_considered),
    )


def _translate_action(llm: _LLMActionAtom) -> ActionAtom:
    context_attrs: dict[str, AttributeAtom] = {}
    for ca in llm.context_attributes:
        # Context attributes are not owned by any entity; we still create an
        # AttributeAtom for them so the data model is uniform.
        context_attrs[ca.field_name] = AttributeAtom(
            name=f"{llm.name}__context__{ca.field_name}",
            rationale=ca.rationale or f"context attribute on action {llm.name}",
            plain_english_summary=ca.plain_english_summary,
            source_excerpt=llm.source_excerpt,
            on_entity="",
            field_name=ca.field_name,
            cedar_type=ca.cedar_type,
            optional=ca.optional,
        )
    return ActionAtom(
        name=llm.name,
        rationale=llm.rationale,
        plain_english_summary=llm.plain_english_summary,
        source_excerpt=llm.source_excerpt,
        principal_types=list(llm.principal_types),
        resource_types=list(llm.resource_types),
        context_attributes=context_attrs,
        parent_groups=list(llm.parent_groups),
    )


def _translate_type_alias(llm: _LLMTypeAliasAtom) -> TypeAliasAtom:
    return TypeAliasAtom(
        name=llm.name,
        rationale=llm.rationale,
        plain_english_summary=llm.plain_english_summary,
        source_excerpt=llm.source_excerpt,
        cedar_type=llm.cedar_type,
    )


def _translate_atom(llm_atom: Any) -> Stage1Atom:
    if isinstance(llm_atom, _LLMEntityAtom):
        return _translate_entity(llm_atom)
    if isinstance(llm_atom, _LLMAttributeAtom):
        return _translate_attribute(llm_atom)
    if isinstance(llm_atom, _LLMActionAtom):
        return _translate_action(llm_atom)
    if isinstance(llm_atom, _LLMTypeAliasAtom):
        return _translate_type_alias(llm_atom)
    raise TypeError(f"unknown LLM atom kind: {type(llm_atom).__name__}")


def _translate_property_atom(llm: _LLMPropertyAtom) -> PropertyAtom:
    reference_cedar = llm.reference_cedar
    disjoint_with = llm.disjoint_with
    if llm.constraint_type == "disjointness":
        reference_cedar = _normalize_disjointness_reference(llm)
        if not disjoint_with and llm.disjoint_target_body:
            disjoint_with = f"{llm.name}_target"
    return PropertyAtom(
        name=llm.name,
        rationale=llm.rationale,
        plain_english_summary=llm.plain_english_summary,
        source_excerpt=llm.source_excerpt,
        constraint_type=llm.constraint_type,
        action=llm.action,
        principal_types=list(llm.principal_types),
        resource_types=list(llm.resource_types),
        reference_cedar=reference_cedar,
        required_schema_support=[
            RequiredSchemaSupport(
                kind=s.kind,
                name=s.name,
                entity=s.entity,
                action=s.action,
                field_name=s.field_name,
                type_name=s.type_name,
                reason=s.reason,
            )
            for s in llm.required_schema_support
        ],
        examples_adversarial=[
            Example(
                description=e.description,
                request_dict=dict(e.request_dict),
                decision_under_chosen=e.decision_under_chosen,
                decisions_under_alternatives=dict(e.decisions_under_alternatives),
                diagnostic_for=list(e.diagnostic_for),
            )
            for e in llm.examples_adversarial
        ],
        alternatives_considered=[
            AlternativeEncoding(
                label=a.label,
                interpretive_choice=a.interpretive_choice,
                cedar_text=a.cedar_text,
            )
            for a in llm.alternatives_considered
        ],
        rate_limit_window=llm.rate_limit_window,
        rate_limit_threshold=llm.rate_limit_threshold,
        rate_limit_counter_attr=llm.rate_limit_counter_attr,
        disjoint_with=disjoint_with,
        disjoint_target_body=llm.disjoint_target_body,
    )


def _normalize_disjointness_reference(llm: _LLMPropertyAtom) -> str:
    """Render disjointness as the primitive ceiling form AutoCedar verifies.

    The reviewable disjointness signal is ``disjoint_target_body``: the Cedar
    boolean condition that must be excluded from otherwise-permitted floors.
    The harness represents that signal as an ``implies`` ceiling whose
    reference permits exactly the complement of the target body. Models often
    reach for literal ``forbid`` policies because the prose says "cannot"; that
    shape is semantically understandable but vacuous for the verifier's
    permit-based satisfiability check, so canonicalize it here.
    """
    target = (llm.disjoint_target_body or "").strip()
    reference = (llm.reference_cedar or "").strip()
    if not target:
        return reference
    if _reference_negates_disjoint_target(reference, target):
        return reference
    principal = llm.principal_types[0] if llm.principal_types else ""
    resource = llm.resource_types[0] if llm.resource_types else ""
    principal_fragment = f"principal is {principal}" if principal else "principal"
    resource_fragment = f"resource is {resource}" if resource else "resource"
    action = llm.action if llm.action.startswith("Action::") else f'Action::"{llm.action}"'
    return (
        f"permit ({principal_fragment}, action == {action}, {resource_fragment})\n"
        f"when {{ !({target}) }};"
    )


def _reference_negates_disjoint_target(reference: str, target: str) -> bool:
    compact_reference = " ".join(reference.split())
    compact_target = " ".join(target.split())
    return f"!({compact_target})" in compact_reference or f"!{compact_target}" in compact_reference


# ---------------------------------------------------------------------------
# LLMClient — the dependency-injection seam.
# ---------------------------------------------------------------------------


class LLMClient:
    """Thin wrapper around AutoCedar's configured LLM provider.

    Construction:
      - ``client``: an ``anthropic.Anthropic`` instance, ``CodexAuthClient``,
        or any object exposing ``.messages.parse(**kwargs)``.
      - ``provider``: ``"anthropic"`` or ``"codex"``. When omitted, reads
        ``AUTOCEDAR_PROVIDER`` and defaults to Codex.
      - ``model``: optional model identifier; when omitted, defaults to the selected provider's
        default model. For Codex this is ``AUTOCEDAR_CODEX_MODEL`` or
        ``gpt-5.5``; for Anthropic this is ``claude-opus-4-7`` unless
        overridden by ``AUTOCEDAR_MODEL`` / ``AUTOCEDAR_AUTHOR_MODEL``.
      - ``max_tokens``: per-call ceiling; defaults to 16000.
      - ``effort``: ``"low" | "medium" | "high" | "max"``; defaults to
        ``"high"`` per the skill guidance for intelligence-sensitive
        workloads.

    Tests pass a mock ``client`` whose ``.messages.parse(...)`` returns
    a hand-crafted response with ``.parsed_output`` populated. No
    network access required.
    """

    def __init__(
        self,
        *,
        client: Optional[Any] = None,
        provider: str | None = None,
        model: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        effort: str = DEFAULT_EFFORT,
    ) -> None:
        resolved_provider = (provider or default_provider()).strip().lower()
        if model is None:
            model = default_model_for_provider(resolved_provider)
        if client is None:
            if is_codex_provider(resolved_provider):
                client = CodexAuthClient()
            else:
                # Lazy-import the SDK so tests can run without ANTHROPIC_API_KEY
                # set; only the live path requires it.
                import anthropic

                client = anthropic.Anthropic()
        self._client = client
        self._provider = resolved_provider
        self._model = model
        self._max_tokens = max_tokens
        self._effort = effort

    # ------------------------------------------------------------------
    # Stage 1: schema atom proposal.
    # ------------------------------------------------------------------

    def propose_schema_atoms(self, spec_text: str) -> list[Stage1Atom]:
        """Ask the LLM to propose Stage 1 atoms for a prose spec.

        The system prompt + spec block are marked ``cache_control``
        ``ephemeral`` so repeated calls in the same session amortize
        the input-token cost (per skill §Prompt Caching). The minimum
        cacheable prefix on Opus 4.7 is 4096 tokens — short specs will
        silently bypass the cache, which is harmless.
        """
        system_prompt = _load_prompt("schema_atomization.md")
        response = self._call_parse(
            system_prompt=system_prompt,
            spec_text=spec_text,
            user_turn=(
                "Propose the Stage 1 schema atoms for the spec above. "
                "Order them so each AttributeAtom appears AFTER the "
                "EntityAtom it lives on, and so ActionAtoms appear "
                "after the entities they reference."
            ),
            output_format=SchemaAtomsResponse,
        )
        return [_translate_atom(a) for a in response.parsed_output.atoms]

    # ------------------------------------------------------------------
    # Stage 2: property atom proposal.
    # ------------------------------------------------------------------

    def propose_property_atom(
        self,
        spec_text: str,
        schema_text: str,
        *,
        prior_atoms: list[PropertyAtom] | None = None,
        prior_decisions: list[Any] | None = None,
    ) -> Optional[PropertyAtom]:
        """Ask the LLM for exactly one next Stage 2 property atom.

        Stage 2 is intentionally a one-atom protocol: the model proposes the
        next property, the verifier checks that property, the human reviews it,
        and only then do we ask for another. This keeps the model context
        aligned with the HITL review unit instead of asking for a monolithic
        list of property/reference pairs.
        """
        prior_atoms = prior_atoms or []
        prior_decisions = prior_decisions or []
        system_prompt = _load_prompt("property_atomization.md")
        prior_json = [_summarize_property_atom(atom) for atom in prior_atoms]
        decision_json = [_summarize_atom_decision(decision) for decision in prior_decisions]
        coverage_instruction = _property_coverage_instruction(prior_atoms)
        response = self._call_parse(
            system_prompt=system_prompt,
            spec_text=spec_text,
            user_turn=(
                "Use this validated Cedar schema as the grounding context:\n\n"
                f"```cedarschema\n{schema_text}\n```\n\n"
                "Already-approved property atoms:\n\n"
                f"```json\n{json.dumps(prior_json, indent=2)}\n```\n\n"
                "Prior review decisions and rejected proposals:\n\n"
                f"```json\n{json.dumps(decision_json, indent=2)}\n```\n\n"
                f"Coverage instruction for this next atom: {coverage_instruction}\n\n"
                "Propose exactly ONE next Stage 2 property atom for HITL review, "
                "or return an empty `atoms` list if the approved atoms already "
                "cover the spec. The property atom is the review unit. Focus on "
                "one source requirement and attach only the signal/context needed "
                "to verify that requirement. Do not bundle multiple requirements "
                "into one atom. Do not emit a duplicate of an approved or rejected "
                "atom. Non-liveness atoms must include a complete `reference_cedar` "
                "policy. Liveness atoms should include a concrete probe policy "
                "when the requirement names a slice that must remain possible; "
                "leave it empty only for broad legacy liveness."
            ),
            output_format=PropertyAtomsResponse,
            effort_override=_stage2_effort(self._provider, self._effort),
        )
        atoms = response.parsed_output.atoms
        if not atoms:
            return None
        return _translate_property_atom(atoms[0])

    def propose_property_atoms(
        self,
        spec_text: str,
        schema_text: str,
        *,
        prior_atoms: list[PropertyAtom] | None = None,
        prior_decisions: list[Any] | None = None,
    ) -> list[PropertyAtom]:
        """Ask the LLM for a bounded local bundle of Stage 2 atoms.

        The bundle is a planner optimization, not a review shortcut: the
        runtime still symbolically verifies and HITL-reviews each returned atom
        one at a time. The model should use this only to cover the current
        source packet, typically returning the floor plus matching
        ceiling/safety/liveness atoms for the same bounded grant.
        """
        prior_atoms = prior_atoms or []
        prior_decisions = prior_decisions or []
        system_prompt = _load_prompt("property_atomization.md")
        prior_json = [_summarize_property_atom(atom) for atom in prior_atoms]
        decision_json = [_summarize_atom_decision(decision) for decision in prior_decisions]
        coverage_instruction = _property_coverage_instruction(prior_atoms)
        response = self._call_parse(
            system_prompt=system_prompt,
            spec_text=spec_text,
            user_turn=(
                "Use this validated Cedar schema as the grounding context:\n\n"
                f"```cedarschema\n{schema_text}\n```\n\n"
                "Already-approved property atoms:\n\n"
                f"```json\n{json.dumps(prior_json, indent=2)}\n```\n\n"
                "Prior review decisions and rejected proposals:\n\n"
                f"```json\n{json.dumps(decision_json, indent=2)}\n```\n\n"
                f"Coverage instruction for this source packet: {coverage_instruction}\n\n"
                "Propose a COMPLETE LOCAL BUNDLE of materially distinct Stage 2 "
                "property atoms for this packet's focus source node, or return an "
                "empty `atoms` list if approved atoms already cover it. The bundle "
                "should normally include both sides of each bounded grant: floor "
                "atoms for required access plus matching ceiling, disjointness, "
                "or liveness atoms for the approved safety boundary. Keep every "
                "atom narrow and independently reviewable; the runtime will review "
                "and verify them one at a time. Do not include requirements from "
                "outside the packet, do not emit duplicates, and do not merge "
                "several source requirements into one atom. Non-liveness atoms "
                "must include complete `reference_cedar` policies. Liveness atoms "
                "should include a concrete probe policy when the requirement names "
                "a slice that must remain possible."
            ),
            output_format=PropertyAtomsResponse,
            effort_override=_stage2_effort(self._provider, self._effort),
        )
        return [_translate_property_atom(atom) for atom in response.parsed_output.atoms]

    def propose_alternative_property_atom(
        self,
        rejected_atom: PropertyAtom,
        user_reason: str,
        spec_text: str,
        schema_text: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> Optional[PropertyAtom]:
        """Propose a replacement for a rejected Stage 2 property atom."""
        from autocedar.atoms import to_dict as _atom_to_dict

        prior_atoms = prior_atoms or []
        rejected_json = _atom_to_dict(rejected_atom)
        prior_json = [_atom_to_dict(atom) for atom in prior_atoms]
        user_turn = (
            "Use this validated Cedar schema as the grounding context:\n\n"
            f"```cedarschema\n{schema_text}\n```\n\n"
            "The user rejected this Stage 2 property atom:\n\n"
            f"```json\n{json.dumps(rejected_json, indent=2)}\n```\n\n"
            f"Their reason: {user_reason}\n\n"
            "Already-approved property atoms, which the replacement must remain "
            "consistent with:\n\n"
            f"```json\n{json.dumps(prior_json, indent=2)}\n```\n\n"
            "Propose ONE replacement property atom that addresses the user's "
            "concern. Preserve the same source requirement, action, principal "
            "types, resource types, and constraint_type unless the user's reason "
            "explicitly asks to change or drop one of those. If the rejected atom "
            "was a floor with missing conditions, return a repaired floor; if it "
            "was a ceiling with missing conditions, return a repaired ceiling. "
            "Use a fresh atom name when changing semantics, and avoid reusing the "
            "name of any already-approved atom. Return a PropertyAtomsResponse "
            "with a single atom. If no replacement should be proposed, return "
            "an empty atoms list."
        )
        response = self._call_parse(
            system_prompt=_load_prompt("property_atomization.md"),
            spec_text=spec_text,
            user_turn=user_turn,
            output_format=PropertyAtomsResponse,
            effort_override=_stage2_effort(self._provider, self._effort),
        )
        atoms = response.parsed_output.atoms
        if not atoms:
            return None
        return _translate_property_atom(atoms[0])

    def plan_property_rejection(
        self,
        *,
        current_atom: PropertyAtom,
        user_reason: str,
        spec_text: str,
        schema_text: str,
        prior_atoms: list[PropertyAtom],
        symbolic_log: list[str],
    ) -> PropertyRejectionPlanResponse:
        """Classify a HITL property rejection into a structured repair action."""
        from autocedar.atoms import to_dict as _atom_to_dict

        prior_json = [_atom_to_dict(atom) for atom in prior_atoms]
        current_json = _atom_to_dict(current_atom)
        user_turn = (
            "A reviewer rejected the current Stage 2 property atom. Decide what "
            "AutoCedar should do next. Do not infer from keywords; reason about "
            "the source packet, current atom, prior approved atoms, verifier log, "
            "and reviewer explanation.\n\n"
            "Allowed actions:\n"
            "- repair_current_property: current atom captures real intent but its "
            "encoding/direction/scope needs repair.\n"
            "- repair_prior_property: current atom is valid, but one named prior "
            "approved property must be revised, widened, narrowed, or merged.\n"
            "- repair_schema: the current schema cannot express the required intent.\n"
            "- reject_current: current atom is not wanted intent and should be skipped.\n"
            "- ask_user_clarification: the intent cannot be resolved from the packet.\n\n"
            "If the symbolic log contains `identity-consistency: FAILED`, treat "
            "it as a role/base identity-model error, not as a normal type error. "
            "Cedar validates entity equality across entity types, but "
            "`User::alice` is not `Patient::alice`. Choose `repair_schema` when "
            "the schema lacks bridge fields such as `Patient.user: User` or "
            "`LicensedHealthCareProfessional.user: User`; choose "
            "`repair_current_property` when the bridge exists but the atom used "
            "a direct cross-type comparison such as `principal == "
            "resource.patient`, `principal == context.patient`, "
            "`resource.sender == principal`, or `context.session.user == "
            "principal`.\n\n"
            "If action is repair_prior_property, set target_atom to the exact "
            "name of the prior atom to repair. If action is repair_schema, fill "
            "schema_gap_summary with the missing schema concept. Always provide "
            "a concrete repair_instruction.\n\n"
            "Current property atom:\n"
            f"```json\n{json.dumps(current_json, indent=2)}\n```\n\n"
            "Reviewer reason:\n"
            f"{user_reason}\n\n"
            "Symbolic verifier log for current atom:\n"
            f"```json\n{json.dumps(symbolic_log, indent=2)}\n```\n\n"
            "Prior approved property atoms:\n"
            f"```json\n{json.dumps(prior_json, indent=2)}\n```\n\n"
            "Validated Cedar schema:\n"
            f"```cedarschema\n{schema_text}\n```"
        )
        response = self._call_parse(
            system_prompt=_load_prompt("property_atomization.md"),
            spec_text=spec_text,
            user_turn=user_turn,
            output_format=PropertyRejectionPlanResponse,
            effort_override=_stage2_effort(self._provider, self._effort),
        )
        return response.parsed_output

    # ------------------------------------------------------------------
    # Stage 1 fix: ask the LLM to fix a cedar-validate failure.
    # ------------------------------------------------------------------

    def answer_question_about_atom(
        self,
        atom: Any,
        question: str,
        spec_text: str,
    ) -> str:
        """Answer a user's free-text question about one reviewed atom.

        Used by the interactive review loop's ``[Q]`` key. The atom is
        rendered as JSON in the user turn so the model has the full
        context (rationale, plain English, source excerpt, fields).
        Returns plain text — no structured output needed.
        """
        from autocedar.atoms import to_dict as _atom_to_dict

        atom_json = _atom_to_dict(atom)
        is_property_atom = isinstance(atom, PropertyAtom)
        atom_stage = "Stage 2 property atom" if is_property_atom else "Stage 1 schema atom"
        user_turn = (
            f"The user is reviewing this {atom_stage}:\n\n"
            f"```json\n{atom_json}\n```\n\n"
            f"They ask: {question}\n\n"
            "Answer their question in 1–3 sentences. Stay focused on "
            "this atom and the spec; do not propose changes unless the "
            "user explicitly asks for one."
        )
        response = self._call_text(
            system_prompt=_load_prompt(
                "property_atomization.md" if is_property_atom else "schema_atomization.md",
            ),
            spec_text=spec_text,
            user_turn=user_turn,
        )
        return response

    def propose_alternative_atom(
        self,
        rejected_atom: Stage1Atom,
        user_reason: str,
        spec_text: str,
    ) -> Optional[Stage1Atom]:
        """Propose a replacement for an atom the user rejected.

        Used by the interactive review loop's ``[R]`` key. Returns the
        first atom in the LLM's response (always re-using the same
        ``SchemaAtomsResponse`` schema for consistency), or ``None`` if
        the LLM declined to propose an alternative.
        """
        from autocedar.atoms import to_dict as _atom_to_dict

        atom_json = _atom_to_dict(rejected_atom)
        user_turn = (
            "The user rejected this Stage 1 atom:\n\n"
            f"```json\n{atom_json}\n```\n\n"
            f"Their reason: {user_reason}\n\n"
            "Propose ONE replacement atom of the same kind that "
            "addresses the user's concern. Return your proposal in "
            "the same SchemaAtomsResponse format (atoms list with a "
            "single entry). If you cannot improve on the rejected "
            "atom, return an empty atoms list."
        )
        response = self._call_parse(
            system_prompt=_load_prompt("schema_atomization.md"),
            spec_text=spec_text,
            user_turn=user_turn,
            output_format=SchemaAtomsResponse,
        )
        atoms = response.parsed_output.atoms
        if not atoms:
            return None
        return _translate_atom(atoms[0])

    def fix_schema(
        self,
        schema_text: str,
        cedar_error_message: str,
        spec_text: str,
    ) -> str:
        """Ask the LLM to fix a schema that ``cedar validate`` rejected.

        Returns the corrected schema text. The schema-fix prompt is a
        separate template; we keep the cache-controlled (system + spec)
        block consistent across calls so the cache continues to hit
        across propose/fix turns.
        """
        system_prompt = _load_prompt("schema_atomization.md")
        user_turn = (
            "The schema you proposed failed `cedar validate`. The "
            "validator error is:\n\n"
            f"```\n{cedar_error_message}\n```\n\n"
            "The current schema is:\n\n"
            f"```cedarschema\n{schema_text}\n```\n\n"
            "Produce a corrected schema. Keep the entity, attribute, "
            "action, and type-alias structure as close as possible to "
            "what you proposed previously — fix only what the validator "
            "rejected."
        )
        response = self._call_parse(
            system_prompt=system_prompt,
            spec_text=spec_text,
            user_turn=user_turn,
            output_format=SchemaFixResponse,
        )
        return response.parsed_output.fixed_schema_text

    # ------------------------------------------------------------------
    # Internal: shared parse helper.
    # ------------------------------------------------------------------

    def _call_parse(
        self,
        *,
        system_prompt: str,
        spec_text: str,
        user_turn: str,
        output_format: type[BaseModel],
        effort_override: str | None = None,
    ) -> Any:
        """Call ``messages.parse`` with cache-controlled system+spec block.

        Caching layout (per skill §Prompt Caching):

          render order: tools → system → messages

          system: [
            {"type": "text", "text": <stable system prompt>},
            {"type": "text", "text": <spec wrapped in <spec> tags>,
             "cache_control": {"type": "ephemeral"}},   ← cache breakpoint
          ]
          messages: [{"role": "user", "content": <per-turn request>}]
                                                       ← uncached, varies

        Only one breakpoint is needed; the system+spec is the entire
        cached prefix.
        """
        kwargs = self._message_kwargs(
            system_prompt=system_prompt,
            spec_text=spec_text,
            effort_override=effort_override,
        )
        try:
            return self._client.messages.parse(
                **kwargs,
                messages=[{"role": "user", "content": user_turn}],
                output_format=output_format,
            )
        except Exception as exc:
            if not _is_grammar_compilation_timeout(exc):
                raise
            return self._call_parse_json_fallback(
                system_prompt=system_prompt,
                spec_text=spec_text,
                user_turn=user_turn,
                output_format=output_format,
                effort_override=effort_override,
            )

    def _call_parse_json_fallback(
        self,
        *,
        system_prompt: str,
        spec_text: str,
        user_turn: str,
        output_format: type[BaseModel],
        effort_override: str | None = None,
    ) -> Any:
        """Fallback when provider-side structured-output grammar compilation times out."""
        schema_json = json.dumps(output_format.model_json_schema(), indent=2)
        fallback_turn = (
            f"{user_turn}\n\n"
            "The structured-output grammar compiler timed out. Return only a JSON "
            "object matching this JSON Schema. Do not wrap it in Markdown and do "
            "not include explanatory prose.\n\n"
            f"```json\n{schema_json}\n```"
        )
        response = self._client.messages.create(
            **self._message_kwargs(
                system_prompt=system_prompt,
                spec_text=spec_text,
                effort_override=effort_override,
            ),
            messages=[{"role": "user", "content": fallback_turn}],
        )
        text = _first_text_block(response)
        payload = _loads_json_object(text)
        return SimpleNamespace(parsed_output=output_format.model_validate(payload))

    def _call_text(
        self,
        *,
        system_prompt: str,
        spec_text: str,
        user_turn: str,
    ) -> str:
        """Call ``messages.create`` for plain-text output (no Pydantic schema).

        Used by ``answer_question_about_atom``. The cache layout is
        identical to ``_call_parse`` so the system+spec cache is shared
        across propose / fix / answer calls in one session.
        """
        response = self._client.messages.create(
            **self._message_kwargs(system_prompt=system_prompt, spec_text=spec_text),
            messages=[{"role": "user", "content": user_turn}],
        )
        return _first_text_block(response)

    def _message_kwargs(
        self,
        *,
        system_prompt: str,
        spec_text: str,
        effort_override: str | None = None,
    ) -> dict[str, Any]:
        return {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "thinking": {"type": "adaptive"},
            "output_config": {
                "effort": effort_override or self._effort,
            },
            "system": [
                {"type": "text", "text": system_prompt},
                {
                    "type": "text",
                    "text": f"<spec>\n{spec_text}\n</spec>",
                    "cache_control": {"type": "ephemeral"},
                },
            ],
        }


def _stage2_effort(provider: str, configured_effort: str) -> str:
    """Use cheap bounded reasoning for Codex property-level calls."""
    if is_codex_provider(provider):
        return "low"
    return configured_effort


def _summarize_property_atom(atom: PropertyAtom) -> dict[str, Any]:
    return {
        "name": atom.name,
        "constraint_type": atom.constraint_type,
        "action": atom.action,
        "principal_types": list(atom.principal_types),
        "resource_types": list(atom.resource_types),
        "plain_english_summary": atom.plain_english_summary,
        "source_excerpt": atom.source_excerpt,
        "reference_cedar": atom.reference_cedar,
        "required_schema_support": [
            {
                "kind": support.kind,
                "name": support.name,
                "entity": support.entity,
                "action": support.action,
                "field_name": support.field_name,
                "type_name": support.type_name,
                "reason": support.reason,
            }
            for support in atom.required_schema_support
        ],
    }


def _summarize_atom_decision(decision: Any) -> dict[str, Any]:
    return {
        "atom_name": getattr(decision, "atom_name", "?"),
        "action": getattr(decision, "action", "?"),
        "reason": getattr(decision, "reason", ""),
        "edit_delta": getattr(decision, "edit_delta", {}),
    }


def _property_coverage_instruction(prior_atoms: list[PropertyAtom]) -> str:
    counts: dict[str, int] = {}
    for atom in prior_atoms:
        counts[atom.constraint_type] = counts.get(atom.constraint_type, 0) + 1
    floor_atoms = [atom for atom in prior_atoms if atom.constraint_type == "floor"]
    safety_actions = {
        atom.action
        for atom in prior_atoms
        if atom.constraint_type in {"ceiling", "disjointness", "rate_limit"}
    }
    unbounded_floor_atoms = [
        atom for atom in floor_atoms if atom.action and atom.action not in safety_actions
    ]
    if counts.get("floor", 0) == 0:
        return (
            "No approved floor atoms exist yet. If the spec contains any positive "
            "permission language such as 'can', 'may', 'must be able', 'allows', "
            "or a use-case success path, propose one missing floor atom now before "
            "adding more ceilings or disjointness atoms. That floor is only the "
            "first side of a bounded grant; after it is approved, Stage 2 should "
            "surface the matching ceiling/safety side unless the source clearly "
            "says the grant is only an example."
        )
    if unbounded_floor_atoms:
        names = ", ".join(atom.name for atom in unbounded_floor_atoms[:5])
        return (
            "Approved floors exist without any same-action ceiling/disjointness "
            f"yet: {names}. Prefer the missing bounded-grant ceiling/safety side "
            "next. The ceiling should keep the action inside the union of the "
            "approved allowed slices for that action/resource shape; do not emit "
            "a narrow ceiling that would exclude another approved same-action "
            "floor. Propose another floor first only if the source has an "
            "uncovered positive slice that must be included in that same union."
        )
    if counts.get("floor", 0) < counts.get("ceiling", 0) + counts.get("disjointness", 0):
        return (
            "Safety atoms currently outnumber floors. Prefer the next missing "
            "floor for an explicit allowed workflow unless every positive "
            "permission path in the spec already has a floor. This does not "
            "make conditional positive grants floor-only: once a floor exists "
            "for an intended allowed slice, the plan still needs a same-action "
            "ceiling/disjointness that keeps that grant inside the approved "
            "slice unless the source text clearly says it is only an example."
        )
    return (
        "Continue with the most important missing property. Before returning an "
        "empty atoms list, audit existing floors as bounded allowed slices. A "
        "positive conditional grant like a role acting on a related resource "
        "usually needs both the floor and a same-action ceiling/disjointness "
        "covering the same approved slice, unless the source text clearly says "
        "the condition is only an example or non-exhaustive. For multi-slice "
        "actions, the ceiling must be a union of approved slices, not a narrow "
        "local ceiling that would exclude sibling floors. Check each floor body "
        "for role/resource relationship, ownership, team membership, assigned "
        "resource, LAN, strong authentication, current/open periods, "
        "upcoming/not-completed semester boundaries, add/drop windows, eligible "
        "course, no conflict, registered student, completed semester, or other "
        "source-named limits. If any floor has such a boundary but no "
        "same-action ceiling/disjointness contains that same boundary, propose "
        "the missing stricter safety atom next. A same-action ceiling for only "
        "part of the floor body is not enough; each named relationship, "
        "lifecycle, ownership, network, authentication, eligibility, conflict, "
        "assignment, or completion boundary must be covered. Otherwise propose "
        "a floor for an uncovered positive workflow, a ceiling/disjointness for "
        "an uncovered safety boundary, or empty only when both sides are covered."
    )


def _first_text_block(response: Any) -> str:
    # Extract the first text block (skip any thinking blocks).
    for block in response.content:
        if getattr(block, "type", None) == "text":
            return block.text
    return ""


def _is_grammar_compilation_timeout(exc: Exception) -> bool:
    text = str(exc).lower()
    return "grammar compilation timed out" in text


def _loads_json_object(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])
