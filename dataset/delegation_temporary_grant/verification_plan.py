"""Hand-authored verification plan for realworld/delegation_temporary_grant.

Tests the ephemeral-grant delegation pattern with:
  - Optional context attribute (`activeGrant?: Grant`) that must be
    guarded with `has` before any read
  - Datetime comparison on a nested record attribute (expiry check)
  - Per-action scoping (a read grant does not authorize write)
  - Owner fallback path when no grant is present

Hunts failure modes:
  - Policies that read `context.activeGrant.X` without `has` guarding
    (Phase 1.25 + §8.4 validation feedback should catch)
  - Policies that collapse read+write grants into one permit and lose
    the action-scope check
  - Policies that use `==` instead of `>` on expiry (boundary error)
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "read_safety", "description": "read permitted only when (owner OR valid active read grant)", "type": "implies", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "write_safety", "description": "write permitted only when (owner OR valid active write grant)", "type": "implies", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "write_safety.cedar")},
        {"name": "create_grant_safety", "description": "createGrant permitted only when owner", "type": "implies", "principal_type": "User", "action": "Action::\"createGrant\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "create_grant_safety.cedar")},
        {"name": "revoke_grant_safety", "description": "revokeGrant permitted only when owner", "type": "implies", "principal_type": "User", "action": "Action::\"revokeGrant\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "revoke_grant_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "owner_must_read", "description": "Owner MUST read their own resource", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "owner_must_read.cedar")},
        {"name": "owner_must_write", "description": "Owner MUST write their own resource", "type": "floor", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "owner_must_write.cedar")},
        {"name": "active_read_grant_must_permit", "description": "Non-owner with active valid read grant MUST be permitted to read", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "active_read_grant_must_permit.cedar")},
        {"name": "active_write_grant_must_permit", "description": "Non-owner with active valid write grant MUST be permitted to write", "type": "floor", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "active_write_grant_must_permit.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_read", "description": "User+read+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource"},
        {"name": "liveness_write", "description": "User+write+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Resource"},
        {"name": "liveness_create_grant", "description": "User+createGrant+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"createGrant\"", "resource_type": "Resource"},
        {"name": "liveness_revoke_grant", "description": "User+revokeGrant+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"revokeGrant\"", "resource_type": "Resource"},
    ]
