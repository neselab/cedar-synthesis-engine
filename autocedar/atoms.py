"""Atom dataclasses for Stage 1 (schema) and Stage 2 (properties).

The load-bearing distinction is between ``symbolic_verified``
(formal property earned by symcc) and ``intent_acknowledged_by_user``
(human judgment exercised by the user during review).

These dataclasses are mutable. The grounding pipeline (§4) mutates
``symbolic_verified``, ``symbolic_verification_log``, and
``examples_adversarial`` in place; the UI (§6) mutates
``intent_acknowledged_by_user`` on user approval; Stage 2.5 (§7.4)
mutates ``traceback_clauses`` and ``traceback_flags`` after Stage 3
converges.

JSON serialization is provided via ``to_dict``/``from_dict`` helpers
on every dataclass — used by ``corpus`` and the UI's session-resume
plumbing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from typing import Any, Literal, Optional, Type, TypeVar

# ---------------------------------------------------------------------------
# Constraint type literals supported by Stage 2.
# ---------------------------------------------------------------------------

ConstraintType = Literal[
    "ceiling",
    "floor",
    "liveness",
    "rate_limit",
    "disjointness",
]

PRIMITIVE_CONSTRAINTS: tuple[str, ...] = ("ceiling", "floor", "liveness")
SUGAR_CONSTRAINTS: tuple[str, ...] = ("rate_limit", "disjointness")


# ---------------------------------------------------------------------------
# Common base.
# ---------------------------------------------------------------------------

@dataclass
class AtomBase:
    """Fields every atom carries.

    The ``name`` is a stable identifier within a session and is what
    the corpus log keys atoms by. The ``rationale`` is a short
    technical reason; the ``plain_english_summary`` is the primary
    review text shown to non-expert reviewers; the ``source_excerpt``
    is the prose span the agent attributed to this atom (per §9.1
    this attribution is corpus-logged as a first-class field).
    """

    name: str
    rationale: str
    plain_english_summary: str
    source_excerpt: str


# ---------------------------------------------------------------------------
# Stage 1 — schema atoms.
# ---------------------------------------------------------------------------

@dataclass
class AttributeAtom(AtomBase):
    """A single attribute on a single entity, or a single context attribute."""

    on_entity: str  # owning entity name; "" for context attributes
    field_name: str
    cedar_type: str  # e.g. "Long", "Set<String>", "Record{...}", or "User"
    optional: bool = False
    alternatives_considered: list[str] = field(default_factory=list)


@dataclass
class EntityAtom(AtomBase):
    """A single entity declaration in the schema."""

    members_of: list[str] = field(default_factory=list)
    attributes: dict[str, AttributeAtom] = field(default_factory=dict)
    enum_values: Optional[list[str]] = None


@dataclass
class ActionAtom(AtomBase):
    """A single action declaration."""

    principal_types: list[str] = field(default_factory=list)
    resource_types: list[str] = field(default_factory=list)
    context_attributes: dict[str, AttributeAtom] = field(default_factory=dict)
    parent_groups: list[str] = field(default_factory=list)


@dataclass
class TypeAliasAtom(AtomBase):
    """A Cedar ``type X = ...`` alias (e.g. ``type Address = {...}``)."""

    cedar_type: str  # the body of `type X = ...`


# ---------------------------------------------------------------------------
# Stage 2 — property atoms.
# ---------------------------------------------------------------------------

@dataclass
class Example:
    """One concrete request used in atom review.

    Adversarial examples (§4.4) pair the chosen encoding's decision
    with the decisions a panel of plausible alternative encodings
    would make on the same request — the user reads the divergence
    and authorizes the chosen encoding as the intended interpretation.

    The ``request_dict`` is the full Cedar-evaluatable request
    (principal, action, resource, context). The
    ``decisions_under_alternatives`` map keys are
    ``AlternativeEncoding.label`` values.
    """

    description: str
    request_dict: dict[str, Any]
    decision_under_chosen: Literal["permit", "deny"]
    decisions_under_alternatives: dict[str, Literal["permit", "deny"]] = field(
        default_factory=dict,
    )
    diagnostic_for: list[str] = field(default_factory=list)


@dataclass
class AlternativeEncoding:
    """One plausible alternative reading of an atom's prose."""

    label: str  # short kebab-case identifier; e.g. "primary-nurse-only"
    interpretive_choice: str  # one-line description of what differs
    cedar_text: str  # the alternative encoding (used for symcc distinguishing)


SchemaSupportKind = Literal[
    "entity",
    "action",
    "action_principal",
    "action_resource",
    "attribute",
    "context",
]


@dataclass
class RequiredSchemaSupport:
    """One schema hook a property atom depends on.

    Stage 2 proposes property atoms one at a time. Before a property is
    verified or shown for HITL review, the runtime checks these hooks against
    the current schema. Missing hooks are routed through Stage 1 schema repair
    instead of surfacing doomed Cedar to the reviewer.
    """

    kind: SchemaSupportKind
    name: str = ""
    entity: str = ""
    action: str = ""
    field_name: str = ""
    type_name: str = ""
    reason: str = ""


@dataclass
class PropertyAtom(AtomBase):
    """A single property atom (Stage 2 output, before sugar compilation).

    Sugar atoms (``rate_limit``, ``disjointness``) carry their sugar-
    specific fields plus a ``reference_cedar`` that is the result of
    naive compilation by the agent during proposal. The authoritative
    compile-down to primitives happens later in
    ``VerificationPlanDraft.compile`` (§5.3); this atom-local
    encoding is what the user reviews and what symcc grounds.

    Per §1.4: ``symbolic_verified`` and ``intent_acknowledged_by_user``
    are deliberately separate fields. The first is what symcc proved
    about the encoding's formal properties; the second is the user's
    authorization that the encoding faithfully captures their intent.
    """

    constraint_type: ConstraintType
    action: str
    principal_types: list[str] = field(default_factory=list)
    resource_types: list[str] = field(default_factory=list)

    reference_cedar: str = ""
    required_schema_support: list[RequiredSchemaSupport] = field(default_factory=list)

    examples_adversarial: list[Example] = field(default_factory=list)
    alternatives_considered: list[AlternativeEncoding] = field(default_factory=list)

    # Symbolic verification (§4.1 — populated by grounding).
    symbolic_verified: bool = False
    symbolic_verification_log: list[str] = field(default_factory=list)

    # Intent verification (§1.4 — populated by UI on [A]pprove).
    intent_acknowledged_by_user: bool = False

    # Stage 2.5 traceback (§7.4 — populated post-Stage-3).
    traceback_clauses: list[str] = field(default_factory=list)
    traceback_flags: list[str] = field(default_factory=list)

    # Sugar-specific fields. Set only when constraint_type matches.
    rate_limit_window: Optional[str] = None
    rate_limit_threshold: Optional[int] = None
    rate_limit_counter_attr: Optional[str] = None
    disjoint_with: Optional[str] = None
    # The Cedar boolean expression the disjointness atom is disjoint from
    # (the body whose negation appears in ``reference_cedar`` and is
    # appended to every floor on the same action via §8.8 patches).
    disjoint_target_body: Optional[str] = None

    def __post_init__(self) -> None:
        self._validate_sugar_fields()

    def _validate_sugar_fields(self) -> None:
        """Sugar atoms require their specific fields; primitives must not set them."""
        if self.constraint_type == "rate_limit":
            missing = [
                k
                for k in ("rate_limit_window", "rate_limit_threshold", "rate_limit_counter_attr")
                if getattr(self, k) is None
            ]
            if missing:
                raise ValueError(
                    f"rate_limit atom {self.name!r} is missing sugar fields: {missing}",
                )
        elif self.constraint_type == "disjointness":
            missing = [
                k
                for k in ("disjoint_with", "disjoint_target_body")
                if getattr(self, k) is None
            ]
            if missing:
                raise ValueError(
                    f"disjointness atom {self.name!r} is missing sugar fields: {missing}",
                )
        else:
            # Primitive: sugar-specific fields must not be set.
            stray = {
                k: getattr(self, k)
                for k in (
                    "rate_limit_window",
                    "rate_limit_threshold",
                    "rate_limit_counter_attr",
                    "disjoint_with",
                    "disjoint_target_body",
                )
                if getattr(self, k) is not None
            }
            if stray:
                raise ValueError(
                    f"{self.constraint_type} atom {self.name!r} has stray sugar fields: {stray}",
                )


# ---------------------------------------------------------------------------
# Composition objects.
# ---------------------------------------------------------------------------

@dataclass
class SchemaDraft:
    """In-progress schema being assembled from approved Stage 1 atoms.

    The ``to_cedar_schema`` rendering and ``cedar validate`` round-trip
    live in ``autocedar.schema_atomizer``. At the data-model layer this
    class is just the ordered structure of approved atoms.
    """

    entities: dict[str, EntityAtom] = field(default_factory=dict)
    actions: dict[str, ActionAtom] = field(default_factory=dict)
    type_aliases: dict[str, TypeAliasAtom] = field(default_factory=dict)
    consistency_log: list[str] = field(default_factory=list)


@dataclass
class VerificationPlanDraft:
    """In-progress verification plan being assembled from approved Stage 2 atoms.

    ``compile`` resolves sugars to primitives, applies §8.8 patches,
    and produces the artifacts the v1 harness consumes. The
    implementation lives in ``autocedar.property_elicitor`` (§5.3).
    """

    properties: list[PropertyAtom] = field(default_factory=list)


# ---------------------------------------------------------------------------
# JSON (de)serialization.
# ---------------------------------------------------------------------------

T = TypeVar("T")


def to_dict(obj: Any) -> Any:
    """Recursive ``dataclasses.asdict`` that preserves dict and list shapes.

    Used for corpus logging (§9.1) and session-resume persistence.
    """
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_dict(v) for v in obj]
    return obj


def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
    """Construct a dataclass instance from its ``to_dict`` output.

    Handles nested dataclass fields by recursing on the field type.
    Only supports the dataclass families defined in this module
    (atoms, examples, alternatives, drafts).
    """
    if not is_dataclass(cls) or isinstance(cls, type) and cls in _PRIMITIVE_CLASSES:
        # Direct primitive construction.
        pass

    kwargs: dict[str, Any] = {}
    type_hints = {f.name: f.type for f in fields(cls)}  # type: ignore[arg-type]
    for f in fields(cls):  # type: ignore[arg-type]
        if f.name not in data:
            continue
        raw = data[f.name]
        kwargs[f.name] = _coerce(raw, type_hints[f.name])
    return cls(**kwargs)  # type: ignore[arg-type, return-value]


# Primitive classes recognized by the deserializer (for forward refs).
_PRIMITIVE_CLASSES = {
    EntityAtom,
    AttributeAtom,
    ActionAtom,
    TypeAliasAtom,
    Example,
    AlternativeEncoding,
    RequiredSchemaSupport,
    PropertyAtom,
    SchemaDraft,
    VerificationPlanDraft,
}


_TYPE_NAME_TO_CLASS = {c.__name__: c for c in _PRIMITIVE_CLASSES}


def _coerce(raw: Any, type_hint: Any) -> Any:
    """Coerce a raw JSON value to the type indicated by a dataclass field hint.

    Uses string parsing of ``type_hint`` because dataclass fields can store
    string forward references on Python 3.11+. Best-effort: primitive
    types pass through; ``list[X]`` and ``dict[K, V]`` are recursed; bare
    dataclass references are coerced via ``from_dict``.
    """
    if raw is None:
        return None

    hint_str = type_hint if isinstance(type_hint, str) else getattr(type_hint, "__name__", str(type_hint))

    # list[X]
    if hint_str.startswith("list["):
        inner = hint_str[len("list[") : -1]
        return [_coerce(v, inner) for v in raw]

    # dict[K, V]
    if hint_str.startswith("dict["):
        inner = hint_str[len("dict[") : -1]
        # split on the first comma at depth 0
        depth = 0
        sep = -1
        for i, ch in enumerate(inner):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == "," and depth == 0:
                sep = i
                break
        if sep == -1:
            return raw
        v_hint = inner[sep + 1 :].strip()
        return {k: _coerce(v, v_hint) for k, v in raw.items()}

    # Optional[X] / X | None
    if hint_str.startswith("Optional["):
        return _coerce(raw, hint_str[len("Optional[") : -1])

    cls = _TYPE_NAME_TO_CLASS.get(hint_str)
    if cls is not None and isinstance(raw, dict):
        return from_dict(cls, raw)

    return raw
