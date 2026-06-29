"""Executor-side checks for property-required schema hooks.

Stage 2 property atoms can now declare the concrete schema support they need.
The runtime checks those hooks before symbolic verification/HITL review and
routes missing hooks through the existing Stage 1 schema-repair path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from autocedar.atoms import RequiredSchemaSupport


@dataclass(frozen=True)
class MissingSchemaSupport:
    """A required schema hook that is absent from the current schema."""

    support: RequiredSchemaSupport
    detail: str


def missing_schema_support(
    required: list[RequiredSchemaSupport],
    schema_text: str,
) -> list[MissingSchemaSupport]:
    """Return required schema hooks absent from ``schema_text``."""

    missing: list[MissingSchemaSupport] = []
    for support in required:
        ok, detail = _support_present(support, schema_text)
        if not ok:
            missing.append(MissingSchemaSupport(support=support, detail=detail))
    return missing


def describe_missing_schema_support(missing: list[MissingSchemaSupport]) -> str:
    """Render missing hooks into a concise schema-repair instruction."""

    parts: list[str] = []
    for item in missing:
        support = item.support
        label = _support_label(support)
        reason = f" Reason: {support.reason}" if support.reason else ""
        parts.append(f"- {label}: {item.detail}.{reason}")
    return "\n".join(parts)


def _support_present(support: RequiredSchemaSupport, schema_text: str) -> tuple[bool, str]:
    kind = support.kind
    if kind == "entity":
        name = support.name or support.entity or support.type_name
        if _entity_exists(schema_text, name):
            return True, ""
        return False, f"entity `{name}` is not declared"
    if kind == "action":
        name = support.name or support.action
        if _action_block(schema_text, name) is not None:
            return True, ""
        return False, f"action `{name}` is not declared"
    if kind == "attribute":
        if _entity_has_attribute(schema_text, support.entity, support.field_name):
            return True, ""
        return False, f"entity `{support.entity}` lacks attribute `{support.field_name}`"
    if kind == "context":
        if _action_context_has_attribute(schema_text, support.action, support.field_name):
            return True, ""
        return False, f"action `{support.action}` lacks context field `{support.field_name}`"
    if kind == "action_principal":
        if _action_has_type(schema_text, support.action, "principal", support.type_name):
            return True, ""
        return (
            False,
            f"action `{support.action}` does not include principal type `{support.type_name}`",
        )
    if kind == "action_resource":
        if _action_has_type(schema_text, support.action, "resource", support.type_name):
            return True, ""
        return (
            False,
            f"action `{support.action}` does not include resource type `{support.type_name}`",
        )
    return False, f"unsupported schema hook kind `{kind}`"


def _support_label(support: RequiredSchemaSupport) -> str:
    if support.kind in {"entity", "action"}:
        return f"{support.kind} `{support.name or support.entity or support.action}`"
    if support.kind == "attribute":
        return f"attribute `{support.entity}.{support.field_name}`"
    if support.kind == "context":
        return f"context `{support.action}.{support.field_name}`"
    if support.kind in {"action_principal", "action_resource"}:
        role = "principal" if support.kind == "action_principal" else "resource"
        return f"action `{support.action}` {role} `{support.type_name}`"
    return support.kind


def _entity_exists(schema_text: str, name: str) -> bool:
    if not name:
        return False
    return bool(re.search(rf"\bentity\s+{re.escape(name)}\b", schema_text))


def _action_block(schema_text: str, action: str) -> str | None:
    if not action:
        return None
    match = re.search(
        rf"\baction\s+{re.escape(action)}\s+appliesTo\s*\{{(?P<body>.*?)\n?\s*\}};",
        schema_text,
        flags=re.DOTALL,
    )
    return match.group("body") if match else None


def _entity_has_attribute(schema_text: str, entity: str, field_name: str) -> bool:
    if not entity or not field_name:
        return False
    match = re.search(
        rf"\bentity\s+{re.escape(entity)}(?:\s+in\s+\[[^\]]*\])?\s*\{{"
        rf"(?P<body>.*?)"
        rf"\n?\s*\}};",
        schema_text,
        flags=re.DOTALL,
    )
    if not match:
        return False
    return bool(re.search(rf"\b{re.escape(field_name)}\??\s*:", match.group("body")))


def _action_context_has_attribute(schema_text: str, action: str, field_name: str) -> bool:
    body = _action_block(schema_text, action)
    if body is None or not field_name:
        return False
    match = re.search(
        r"\bcontext\s*:\s*\{(?P<body>.*?)\n\s*\},",
        body,
        flags=re.DOTALL,
    )
    if not match:
        return False
    return bool(re.search(rf"\b{re.escape(field_name)}\??\s*:", match.group("body")))


def _action_has_type(schema_text: str, action: str, slot: str, type_name: str) -> bool:
    body = _action_block(schema_text, action)
    if body is None or not type_name:
        return False
    match = re.search(
        rf"\b{re.escape(slot)}\s*:\s*\[(?P<types>[^\]]*)\]",
        body,
        flags=re.DOTALL,
    )
    if not match:
        return False
    types = {
        item.strip()
        for item in match.group("types").replace("\n", " ").split(",")
        if item.strip()
    }
    return type_name in types
