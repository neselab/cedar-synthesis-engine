"""Hand-authored verification plan for realworld/homogeneous_set_type_mismatch.

Tests Cedar's set-homogeneity validator constraint. Set literals in policies
must contain elements of a single type — `[User::"a", "b"]` (entity + string)
and `[]` (no inferable element type) are both rejected by the validator.

The reference policies use two homogeneous set literal shapes:
  - entity-set literal: `[Group::"admins", Group::"auditors", Group::"compliance"]`
  - string-set literal: `["share-allowed", "public"]`

Checks:
  - 2 ceilings (view safety, share safety)
  - 4 floors (view-owner, view-admin-group, share-owner, share-member)
  - 2 liveness (view, share)
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "view_safety",
            "description": "view permitted only when principal in privileged group, owner in privileged group, or principal == owner",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "share_safety",
            "description": "share permitted only when (member or owner) AND aliases overlap allowlisted strings",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"share"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "share_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "floor_view_owner",
            "description": "document owner MUST view",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_view_owner.cedar"),
        },
        {
            "name": "floor_view_admin_group",
            "description": "principal in a privileged group MUST view",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_view_admin_group.cedar"),
        },
        {
            "name": "floor_share_owner",
            "description": "owner with allowlisted alias MUST share",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"share"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_share_owner.cedar"),
        },
        {
            "name": "floor_share_member",
            "description": "member with allowlisted alias MUST share",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"share"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_share_member.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_view",
            "description": "at least one view must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
        },
        {
            "name": "liveness_share",
            "description": "at least one share must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"share"',
            "resource_type": "Document",
        },
    ]
