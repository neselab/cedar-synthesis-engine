"""Identity-model checks for generated Cedar property atoms.

These checks catch a class of bugs that Cedar validation allows: a policy may
compare two schema-valid entity values that are never the same Cedar entity
because their entity types differ, e.g. ``User::"alice" == Patient::"alice"``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from autocedar.atoms import PropertyAtom


_ENTITY_RE = re.compile(
    r"\bentity\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s+in\s+\[(?P<parents>[^\]]*)\])?"
    r"(?:\s*\{(?P<body>.*?)\n?\s*\};|\s*;)",
    re.DOTALL,
)
_ACTION_RE = re.compile(
    r"\baction\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+appliesTo\s*\{(?P<body>.*?)\n?\s*\};",
    re.DOTALL,
)
_FIELD_RE = re.compile(
    r"\b(?P<name>[A-Za-z_][A-Za-z0-9_]*)\??\s*:\s*(?P<type>[A-Za-z_][A-Za-z0-9_]*(?:<[^>]+>)?)"
)
_PRINCIPAL_IS_RE = re.compile(r"\bprincipal\s+is\s+(?P<type>[A-Za-z_][A-Za-z0-9_]*)")
_PERMIT_PRINCIPAL_IS_RE = re.compile(
    r"\bpermit\s*\(\s*principal\s+is\s+(?P<type>[A-Za-z_][A-Za-z0-9_]*)",
    re.DOTALL,
)
_EQUALITY_RE = re.compile(
    r"(?P<left>\bprincipal\b|(?:resource|context)\.[A-Za-z_][A-Za-z0-9_.]*)\s*==\s*"
    r"(?P<right>\bprincipal\b|(?:resource|context)\.[A-Za-z_][A-Za-z0-9_.]*)"
)


@dataclass(frozen=True)
class IdentityIssue:
    """A schema-valid but identity-inconsistent comparison."""

    expression: str
    principal_types: tuple[str, ...]
    path: str
    path_type: str
    detail: str


@dataclass(frozen=True)
class SchemaIdentityIndex:
    """Small schema index sufficient for identity checks."""

    entity_fields: dict[str, dict[str, str]]
    entity_parents: dict[str, set[str]]
    action_context_fields: dict[str, dict[str, str]]

    @classmethod
    def parse(cls, schema_text: str) -> "SchemaIdentityIndex":
        entity_fields: dict[str, dict[str, str]] = {}
        entity_parents: dict[str, set[str]] = {}
        for match in _ENTITY_RE.finditer(schema_text):
            name = match.group("name")
            parents = {
                item.strip()
                for item in (match.group("parents") or "").split(",")
                if item.strip()
            }
            entity_parents[name] = parents
            body = match.group("body") or ""
            entity_fields[name] = {
                field.group("name"): _normalize_type(field.group("type"))
                for field in _FIELD_RE.finditer(body)
            }

        action_context_fields: dict[str, dict[str, str]] = {}
        for match in _ACTION_RE.finditer(schema_text):
            body = match.group("body")
            context = re.search(r"\bcontext\s*:\s*\{(?P<body>.*?)\n\s*\},", body, re.DOTALL)
            if context:
                action_context_fields[match.group("name")] = {
                    field.group("name"): _normalize_type(field.group("type"))
                    for field in _FIELD_RE.finditer(context.group("body"))
                }

        return cls(
            entity_fields=entity_fields,
            entity_parents=entity_parents,
            action_context_fields=action_context_fields,
        )

    def path_type(self, atom: PropertyAtom, path: str) -> str | None:
        parts = path.split(".")
        if len(parts) < 2:
            return None
        root, first = parts[0], parts[1]
        if root == "resource":
            current = atom.resource_types[0] if atom.resource_types else ""
            fields = parts[1:]
        elif root == "context":
            current = self.action_context_fields.get(atom.action, {}).get(first, "")
            fields = parts[2:]
        else:
            return None

        current = _normalize_type(current)
        for field_name in fields:
            field_type = self.entity_fields.get(current, {}).get(field_name)
            if not field_type:
                return None
            current = field_type
        return current or None

    def related_entity_types(self, left: str, right: str) -> bool:
        if left == right:
            return False
        if left not in self.entity_fields or right not in self.entity_fields:
            return False
        return self._is_ancestor(left, right) or self._is_ancestor(right, left)

    def _is_ancestor(self, ancestor: str, child: str) -> bool:
        seen: set[str] = set()
        stack = list(self.entity_parents.get(child, set()))
        while stack:
            item = stack.pop()
            if item == ancestor:
                return True
            if item in seen:
                continue
            seen.add(item)
            stack.extend(self.entity_parents.get(item, set()))
        return False


def find_identity_issues(atom: PropertyAtom, schema_text: str) -> list[IdentityIssue]:
    """Return role/base identity mismatches in ``atom.reference_cedar``.

    The check focuses on equality with ``principal`` because that is where
    generated policies most often conflate account identity (``User``) with a
    role/profile entity (``Patient``, ``LicensedHealthCareProfessional``, etc.).
    """

    if atom.constraint_type == "liveness" or not atom.reference_cedar:
        return []

    index = SchemaIdentityIndex.parse(schema_text)
    principal_types = _principal_types_in_policy(atom)
    issues: list[IdentityIssue] = []
    for match in _EQUALITY_RE.finditer(atom.reference_cedar):
        left = match.group("left")
        right = match.group("right")
        if left == "principal":
            path = right
        elif right == "principal":
            path = left
        else:
            continue
        path_type = index.path_type(atom, path)
        if not path_type:
            continue
        principal_types = _principal_types_for_equality(
            atom,
            atom.reference_cedar,
            match.start(),
        )
        mismatched = [
            ptype
            for ptype in principal_types
            if index.related_entity_types(ptype, path_type)
        ]
        if not mismatched:
            continue
        issues.append(
            IdentityIssue(
                expression=match.group(0),
                principal_types=tuple(mismatched),
                path=path,
                path_type=path_type,
                detail=(
                    "Cross-type entity equality between principal type(s) "
                    f"{', '.join(mismatched)} and `{path}` of type `{path_type}`. "
                    "Cedar entity equality is type-sensitive; use one canonical "
                    "principal identity or compare through an explicit bridge field."
                ),
            ),
        )
    return issues


def format_identity_issues(issues: list[IdentityIssue]) -> str:
    return "\n".join(
        f"{issue.expression}: {issue.detail}"
        for issue in issues
    )


def _principal_types_in_policy(atom: PropertyAtom) -> list[str]:
    constrained = [match.group("type") for match in _PERMIT_PRINCIPAL_IS_RE.finditer(atom.reference_cedar)]
    return _dedupe(constrained or atom.principal_types)


def _principal_types_for_equality(
    atom: PropertyAtom,
    reference_cedar: str,
    equality_start: int,
) -> list[str]:
    """Infer the principal type active at one equality expression.

    Most generated union policies are written as ``branch || branch`` with each
    branch starting with ``principal is Type``. Looking only at the whole policy
    causes false positives, so first inspect the local disjunct around the
    equality and then fall back to the permit head / atom metadata.
    """

    before_or = reference_cedar.rfind("||", 0, equality_start)
    after_or = reference_cedar.find("||", equality_start)
    start = 0 if before_or == -1 else before_or + 2
    end = len(reference_cedar) if after_or == -1 else after_or
    local = reference_cedar[start:end]
    local_types = [match.group("type") for match in _PRINCIPAL_IS_RE.finditer(local)]
    if local_types:
        return _dedupe(local_types)
    return _principal_types_in_policy(atom)


def _normalize_type(type_name: str) -> str:
    type_name = type_name.strip()
    set_match = re.fullmatch(r"Set<\s*([A-Za-z_][A-Za-z0-9_]*)\s*>", type_name)
    if set_match:
        return set_match.group(1)
    return type_name


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out
