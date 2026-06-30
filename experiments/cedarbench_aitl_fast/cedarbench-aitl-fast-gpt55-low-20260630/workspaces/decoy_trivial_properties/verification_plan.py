"""Hand-authored verification plan for realworld/decoy_trivial_properties.

Stress-tests the harness with a plan that mixes a small number of
substantive checks (1 ceiling, 3 hard floors, 1 liveness) with 5
trivially-true floors. The trivial floors are vacuously satisfied by
any candidate that permits at least one request.

Total: 1 ceiling + 3 hard floors + 5 trivial floors + 1 liveness = 10 checks.

The substantive checks pin the candidate to:

    principal.role == "admin"
    || (principal.role == "user" && resource.level <= 3)

The trivial floors should always show PASS without consuming iteration
budget on candidate revisions.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Hard ceiling ─────────────────────────────────────────────────
        {
            "name": "access_ceiling",
            "description": "access permit must satisfy role==admin OR (role==user AND level<=3)",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "access_ceiling.cedar"),
        },

        # ── Hard floors ──────────────────────────────────────────────────
        {
            "name": "admin_any_level_must_permit",
            "description": "An admin must be permitted to access any resource at any level",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "admin_any_level_must_permit.cedar"),
        },
        {
            "name": "user_low_level_must_permit",
            "description": "A user (role==user) with resource.level <= 3 must be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "user_low_level_must_permit.cedar"),
        },
        {
            "name": "user_zero_level_must_permit",
            "description": "A user (role==user) accessing a resource with level == 0 must be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "user_zero_level_must_permit.cedar"),
        },

        # ── Trivially-true floors (decoy; should PASS for any sound candidate) ──
        {
            "name": "trivial_floor_true",
            "description": "Trivial: permit when true (vacuously satisfied)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "trivial_floor_true.cedar"),
        },
        {
            "name": "trivial_floor_one_eq_one",
            "description": "Trivial: permit when 1 == 1 (vacuously satisfied)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "trivial_floor_one_eq_one.cedar"),
        },
        {
            "name": "trivial_floor_string_eq",
            "description": "Trivial: permit when \"x\" == \"x\" (vacuously satisfied)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "trivial_floor_string_eq.cedar"),
        },
        {
            "name": "trivial_floor_or_true",
            "description": "Trivial: permit when (1 == 2) || true (vacuously satisfied)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "trivial_floor_or_true.cedar"),
        },
        {
            "name": "trivial_floor_not_false",
            "description": "Trivial: permit when !(1 == 2) (vacuously satisfied)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "trivial_floor_not_false.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_access",
            "description": "User+access+Resource has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
        },
    ]
