"""Hand-authored verification plan for realworld/conditional_role_activation.

Geo-fenced role activation: the elevated `admin` role is only "active"
when the request comes from the office network (context attestation)
AND the principal has the office-network authorization flag set
(principal attribute). Both conditions plus `homeRole == "admin"` are
required for adminConfig.

Hunts for the failure mode where the model treats `homeRole == "admin"`
alone as sufficient, or omits one of the two activation gates.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "read_safety", "description": "read permitted for any Employee on a SecureSystem", "type": "implies", "principal_type": "Employee", "action": "Action::\"read\"", "resource_type": "SecureSystem", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "adminConfig_safety", "description": "adminConfig permitted only when admin homeRole AND connectedFromOffice AND officeNetworkAuth", "type": "implies", "principal_type": "Employee", "action": "Action::\"adminConfig\"", "resource_type": "SecureSystem", "reference_path": os.path.join(REFS, "adminConfig_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "read_must_permit", "description": "Any Employee MUST be permitted to read a SecureSystem", "type": "floor", "principal_type": "Employee", "action": "Action::\"read\"", "resource_type": "SecureSystem", "floor_path": os.path.join(REFS, "read_must_permit.cedar")},
        {"name": "admin_with_activation_must_permit", "description": "Admin Employee with officeNetworkAuth, connecting from office, MUST be permitted to adminConfig", "type": "floor", "principal_type": "Employee", "action": "Action::\"adminConfig\"", "resource_type": "SecureSystem", "floor_path": os.path.join(REFS, "admin_with_activation_must_permit.cedar")},
        {"name": "admin_can_also_read_must_permit", "description": "An admin Employee MUST also be permitted to read", "type": "floor", "principal_type": "Employee", "action": "Action::\"read\"", "resource_type": "SecureSystem", "floor_path": os.path.join(REFS, "admin_can_also_read_must_permit.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_read", "description": "Employee+read+SecureSystem liveness", "type": "always-denies-liveness", "principal_type": "Employee", "action": "Action::\"read\"", "resource_type": "SecureSystem"},
        {"name": "liveness_adminConfig", "description": "Employee+adminConfig+SecureSystem liveness", "type": "always-denies-liveness", "principal_type": "Employee", "action": "Action::\"adminConfig\"", "resource_type": "SecureSystem"},
    ]
