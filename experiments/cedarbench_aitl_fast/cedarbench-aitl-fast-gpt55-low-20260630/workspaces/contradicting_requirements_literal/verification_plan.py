"""Hand-authored verification plan for realworld/contradicting_requirements_literal.

This scenario is deliberately constructed to stress-test the §8.8
floor-bound consistency rule against a spec that contains TWO
requirements that literally contradict, resolved by an explicit
precedence rule.

Requirement A: "Owners must always be able to view their own documents."
Requirement B: "Documents marked as 'quarantined' must NEVER be viewable."
Precedence: quarantine wins (security forbids over access permits).

A naive planner that writes a `floor_owner` of just
`permit when principal == resource.owner` would create jointly
unsatisfiable bounds against the quarantine ceiling. The careful
planner (this file) carves the owner floor with `!resource.quarantined`,
producing satisfiable bounds.

Critically, NO floor for the contradicting case
(`principal == resource.owner && resource.quarantined`) exists —
that case is resolved by the precedence rule into denial, and any
floor asserting permission there would be UNSAT against the ceiling.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "view_safety",
            "description": "view permitted only when document is not quarantined",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"view\"",
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "owner_must_view_unquarantined",
            "description": "Owner MUST view their own document UNLESS quarantined (§8.8 carve-out)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"view\"",
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "owner_must_view_unquarantined.cedar"),
        },
        {
            "name": "floor_unquarantined_owner_views",
            "description": "Restated post-resolution: for any non-quarantined doc, the owner MUST view (Requirement C)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"view\"",
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_unquarantined_owner_views.cedar"),
        },
        {
            "name": "liveness_view",
            "description": "User+view+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"view\"",
            "resource_type": "Document",
        },
    ]
