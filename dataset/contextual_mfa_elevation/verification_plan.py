"""Hand-authored verification plan for realworld/contextual_mfa_elevation.

Step-up authentication pattern: sensitive actions require a fresh MFA
verification (within 15 minutes), low-risk actions do not. Tests:
  - `datetime.durationSince(other)` method (not tested before)
  - Conditional MFA check that applies to SOME actions but not others
  - Composition of workspace isolation + role + MFA freshness

Hunts for the failure mode where the model forgets the MFA check on
sensitive actions, or applies it universally.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "read_safety", "description": "read permitted only when same workspace", "type": "implies", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "comment_safety", "description": "comment permitted only when same workspace", "type": "implies", "principal_type": "User", "action": "Action::\"comment\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "comment_safety.cedar")},
        {"name": "write_safety", "description": "write permitted only when same workspace", "type": "implies", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "write_safety.cedar")},
        {"name": "delete_safety", "description": "deleteDocument permitted only when same workspace AND MFA fresh (< 15m)", "type": "implies", "principal_type": "User", "action": "Action::\"deleteDocument\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "delete_safety.cedar")},
        {"name": "admin_safety", "description": "adminOperation permitted only when own workspace AND isAdmin AND MFA fresh", "type": "implies", "principal_type": "User", "action": "Action::\"adminOperation\"", "resource_type": "Workspace", "reference_path": os.path.join(REFS, "admin_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "same_workspace_read_must_permit", "description": "User MUST read any document in their workspace", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "same_workspace_read_must_permit.cedar")},
        {"name": "same_workspace_write_must_permit", "description": "User MUST write any document in their workspace", "type": "floor", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "same_workspace_write_must_permit.cedar")},
        {"name": "fresh_mfa_delete_must_permit", "description": "User with fresh MFA MUST delete a document in their own workspace", "type": "floor", "principal_type": "User", "action": "Action::\"deleteDocument\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "fresh_mfa_delete_must_permit.cedar")},
        {"name": "admin_with_fresh_mfa_must_permit", "description": "Admin user with fresh MFA MUST perform adminOperation on own workspace", "type": "floor", "principal_type": "User", "action": "Action::\"adminOperation\"", "resource_type": "Workspace", "floor_path": os.path.join(REFS, "admin_with_fresh_mfa_must_permit.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_read", "description": "User+read+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Document"},
        {"name": "liveness_write", "description": "User+write+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Document"},
        {"name": "liveness_delete", "description": "User+deleteDocument+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"deleteDocument\"", "resource_type": "Document"},
        {"name": "liveness_admin", "description": "User+adminOperation+Workspace liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"adminOperation\"", "resource_type": "Workspace"},
    ]
