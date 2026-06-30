"""Hand-authored verification plan for realworld/priority_based_role_resolution.

Tests priority-based role resolution in Cedar. Users hold a Set<String>
of roles (admin > premium > subscriber > guest). Records have a tier.
Each role has a different set of (action, tier) it may access.

Cedar has no rule-priority mechanism. The correct encoding is a set of
positive permits, one per role's access set; Cedar's permit-union
semantics auto-resolve to the highest-priority outcome when a user
holds multiple roles. The trap: encoding priority via forbids keyed on
lower-priority roles breaks for users holding multiple roles
(harness_fix_log.md §8.6 — role-intersection trap). The
multi_role_subscriber_and_guest_must_view_confidential floor catches
exactly that failure mode.

11 checks total (3 ceilings + 5 floors + 3 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "view_safety", "description": "viewRecord permitted only when some role-tier matrix entry covers (role, tier)", "type": "implies", "principal_type": "User", "action": "Action::\"viewRecord\"", "resource_type": "Record", "reference_path": os.path.join(REFS, "view_safety.cedar")},
        {"name": "edit_safety", "description": "editRecord permitted only when principal holds the admin role", "type": "implies", "principal_type": "User", "action": "Action::\"editRecord\"", "resource_type": "Record", "reference_path": os.path.join(REFS, "edit_safety.cedar")},
        {"name": "delete_safety", "description": "deleteRecord permitted only when principal holds the admin role", "type": "implies", "principal_type": "User", "action": "Action::\"deleteRecord\"", "resource_type": "Record", "reference_path": os.path.join(REFS, "delete_safety.cedar")},

        # ── Floors (positive assertions) ─────────────────────────────────
        {"name": "subscriber_must_view_confidential", "description": "User with role 'subscriber' MUST view a confidential Record", "type": "floor", "principal_type": "User", "action": "Action::\"viewRecord\"", "resource_type": "Record", "floor_path": os.path.join(REFS, "subscriber_must_view_confidential.cedar")},
        {"name": "premium_must_view_premium_only", "description": "User with role 'premium' MUST view a premium-only Record", "type": "floor", "principal_type": "User", "action": "Action::\"viewRecord\"", "resource_type": "Record", "floor_path": os.path.join(REFS, "premium_must_view_premium_only.cedar")},
        {"name": "admin_must_view_admin_only", "description": "User with role 'admin' MUST view an admin-only Record", "type": "floor", "principal_type": "User", "action": "Action::\"viewRecord\"", "resource_type": "Record", "floor_path": os.path.join(REFS, "admin_must_view_admin_only.cedar")},
        {"name": "admin_must_edit_any", "description": "User with role 'admin' MUST edit any Record", "type": "floor", "principal_type": "User", "action": "Action::\"editRecord\"", "resource_type": "Record", "floor_path": os.path.join(REFS, "admin_must_edit_any.cedar")},
        {"name": "multi_role_subscriber_and_guest_must_view_confidential", "description": "PRIORITY TEST: User holding BOTH 'subscriber' and 'guest' MUST view a confidential Record (subscriber overrides guest)", "type": "floor", "principal_type": "User", "action": "Action::\"viewRecord\"", "resource_type": "Record", "floor_path": os.path.join(REFS, "multi_role_subscriber_and_guest_must_view_confidential.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_view_record", "description": "User+viewRecord+Record liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"viewRecord\"", "resource_type": "Record"},
        {"name": "liveness_edit_record", "description": "User+editRecord+Record liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"editRecord\"", "resource_type": "Record"},
        {"name": "liveness_delete_record", "description": "User+deleteRecord+Record liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"deleteRecord\"", "resource_type": "Record"},
    ]
