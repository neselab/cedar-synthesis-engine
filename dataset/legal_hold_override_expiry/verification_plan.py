"""Hand-authored verification plan for realworld/legal_hold_override_expiry.

Records-management pattern with expiry + legal hold interaction. Tests
the conditional override: legal hold preserves edit access past expiry
for the legal team, but legal team has no delete authority even on
held documents.

Safety properties hunted:
  - Legal team must NOT gain edit access to documents NOT under legal hold
  - Legal team must NOT gain delete access regardless of legal hold
  - Owner loses edit AND delete once expired (unless hold logic kicks in)
  - Owner loses delete under legal hold regardless of expiry
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "read_safety", "description": "readDocument permitted only when (owner OR legal team)", "type": "implies", "principal_type": "User", "action": "Action::\"readDocument\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "edit_safety", "description": "editDocument permitted only when ((owner AND pre-expiry) OR (legal team AND legal hold))", "type": "implies", "principal_type": "User", "action": "Action::\"editDocument\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "edit_safety.cedar")},
        {"name": "delete_safety", "description": "deleteDocument permitted only when (owner AND pre-expiry AND NOT legal hold)", "type": "implies", "principal_type": "User", "action": "Action::\"deleteDocument\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "delete_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "owner_must_read", "description": "Owner MUST read their own document", "type": "floor", "principal_type": "User", "action": "Action::\"readDocument\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "owner_must_read.cedar")},
        {"name": "legal_team_must_read", "description": "Legal team member MUST read any document", "type": "floor", "principal_type": "User", "action": "Action::\"readDocument\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "legal_team_must_read.cedar")},
        {"name": "owner_pre_expiry_must_edit", "description": "Owner MUST edit their own document when pre-expiry", "type": "floor", "principal_type": "User", "action": "Action::\"editDocument\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "owner_pre_expiry_must_edit.cedar")},
        {"name": "legal_team_must_edit_on_hold", "description": "Legal team member MUST edit a document under legal hold regardless of expiry", "type": "floor", "principal_type": "User", "action": "Action::\"editDocument\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "legal_team_must_edit_on_hold.cedar")},
        {"name": "owner_pre_expiry_no_hold_must_delete", "description": "Owner MUST delete their document when pre-expiry AND not under legal hold", "type": "floor", "principal_type": "User", "action": "Action::\"deleteDocument\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "owner_pre_expiry_no_hold_must_delete.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_read", "description": "User+readDocument+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"readDocument\"", "resource_type": "Document"},
        {"name": "liveness_edit", "description": "User+editDocument+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"editDocument\"", "resource_type": "Document"},
        {"name": "liveness_delete", "description": "User+deleteDocument+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"deleteDocument\"", "resource_type": "Document"},
    ]
