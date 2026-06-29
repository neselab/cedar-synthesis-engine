"""Small Stage 2 dependency graph artifacts.

The graph is intentionally lightweight: it is not another planner. It records
the approved property atoms, the actions/types they touch, and explicit links
between those formal intent units. This gives experimenters an auditable
"blueprint" layer without changing the Cedar synthesis backend.
"""

from __future__ import annotations

from typing import Any

from autocedar.atoms import PropertyAtom


def build_property_intent_graph(
    properties: list[PropertyAtom],
) -> dict[str, Any]:
    """Return a compact graph of Stage 2 properties and dependencies."""

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []

    def add_node(node_id: str, kind: str, **attrs: Any) -> None:
        existing = nodes.setdefault(node_id, {"id": node_id, "kind": kind})
        existing.update(attrs)

    for atom in properties:
        atom_id = f"property:{atom.name}"
        add_node(
            atom_id,
            "property",
            name=atom.name,
            constraint_type=atom.constraint_type,
            summary=atom.plain_english_summary,
            source_excerpt=atom.source_excerpt,
            symbolic_verified=atom.symbolic_verified,
            intent_acknowledged_by_user=atom.intent_acknowledged_by_user,
        )

        if atom.action:
            action_id = f"action:{atom.action}"
            add_node(action_id, "action", name=atom.action)
            edges.append({"source": atom_id, "target": action_id, "type": "uses_action"})

        for principal_type in atom.principal_types:
            principal_id = f"principal_type:{principal_type}"
            add_node(principal_id, "principal_type", name=principal_type)
            edges.append(
                {"source": atom_id, "target": principal_id, "type": "uses_principal_type"},
            )

        for resource_type in atom.resource_types:
            resource_id = f"resource_type:{resource_type}"
            add_node(resource_id, "resource_type", name=resource_type)
            edges.append(
                {"source": atom_id, "target": resource_id, "type": "uses_resource_type"},
            )

        if atom.disjoint_with:
            disjoint_id = f"property:{atom.disjoint_with}"
            add_node(disjoint_id, "property_ref", name=atom.disjoint_with)
            edges.append({"source": atom_id, "target": disjoint_id, "type": "disjoint_with"})

    return {
        "schema_version": 1,
        "nodes": list(nodes.values()),
        "edges": edges,
        "summary": {
            "properties": len(properties),
        },
    }
