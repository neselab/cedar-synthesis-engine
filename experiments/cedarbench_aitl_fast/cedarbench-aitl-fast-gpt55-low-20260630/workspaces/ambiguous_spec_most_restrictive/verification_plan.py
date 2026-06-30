"""Hand-authored verification plan for realworld/ambiguous_spec_most_restrictive.

This scenario tests whether a planner reading deliberately hedged
natural language ("typically", "may sometimes", "high-impact") chooses
the MOST RESTRICTIVE interpretation consistent with the spec.

The convention codified here:

    When the spec is ambiguous, default to most-restrictive.

Concretely, the references encode:
  - view permitted ONLY when explicitGrant AND role in {admin, user}
  - approve permitted ONLY when explicitGrant AND role == admin

Floors enforce that the spec is not vacuous: an admin-with-grant must
be able to view AND approve, and a user-with-grant must be able to
view. Anything beyond that (e.g. admin without grant, guest with
grant) is forbidden by the ceiling.

If Haiku reads the same hedges and produces the same restrictive
policy, the candidate satisfies all checks. If Haiku reads "typically"
as "by default," the candidate over-permits and a ceiling violation
is reported.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "view_safety",
            "description": "view permitted only when explicitGrant AND role in {admin, user}",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"view\"",
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "approve_safety",
            "description": "approve permitted only when explicitGrant AND role == admin",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"approve\"",
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "approve_safety.cedar"),
        },
        {
            "name": "floor_admin_view",
            "description": "Admin with explicit grant MUST be able to view any document",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"view\"",
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_admin_view.cedar"),
        },
        {
            "name": "floor_user_view",
            "description": "Regular user with explicit grant MUST be able to view any document",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"view\"",
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_user_view.cedar"),
        },
        {
            "name": "floor_admin_approve",
            "description": "Admin with explicit grant MUST be able to approve any document",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"approve\"",
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_admin_approve.cedar"),
        },
        {
            "name": "liveness_view",
            "description": "User+view+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"view\"",
            "resource_type": "Document",
        },
        {
            "name": "liveness_approve",
            "description": "User+approve+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"approve\"",
            "resource_type": "Document",
        },
    ]
