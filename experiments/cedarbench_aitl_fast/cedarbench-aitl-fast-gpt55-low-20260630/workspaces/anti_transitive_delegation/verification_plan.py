"""Hand-authored verification plan for realworld/anti_transitive_delegation.

Tests an anti-transitive delegation pattern with:
  - Optional context attribute (`delegationGrant?`) — must be `has`-guarded
  - A `depth` field on the grant that the policy enforces == 1 (no chains)
  - A separate `delegate` action that is owner-only — even valid depth-1
    grantees cannot themselves re-delegate

Hunts failure modes:
  - Policies that read `context.delegationGrant.X` without `has` guarding
    (Phase 1.25 + §8.4 validation feedback should catch).
  - Policies that consult `delegationGrant` in the `delegate` permit
    (this would let a depth-1 grantee re-delegate, producing an
    implicit depth-2 chain).
  - Policies that use `<= 1` or `>= 1` on the depth check, admitting
    transitive chains (depth >= 2) or zero-depth states.
  - Policies that drop the `delegator == resource.owner` check, honoring
    grants signed by intermediates.
  - Policies that drop the `resource == resource` check, allowing a grant
    issued for resource A to authorize access to resource B.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "read_safety", "description": "read permitted only when (owner OR depth-1 grant from owner naming this resource and principal as delegatee)", "type": "implies", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "write_safety", "description": "write permitted only when (owner OR depth-1 grant from owner naming this resource and principal as delegatee)", "type": "implies", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "write_safety.cedar")},
        {"name": "delegate_safety", "description": "delegate permitted only when principal is the owner — no grant confers delegation authority", "type": "implies", "principal_type": "User", "action": "Action::\"delegate\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "delegate_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "owner_must_read", "description": "Owner MUST be permitted to read their own resource", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "owner_must_read.cedar")},
        {"name": "owner_must_write", "description": "Owner MUST be permitted to write their own resource", "type": "floor", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "owner_must_write.cedar")},
        {"name": "owner_must_delegate", "description": "Owner MUST be permitted to perform `delegate` on their own resource", "type": "floor", "principal_type": "User", "action": "Action::\"delegate\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "owner_must_delegate.cedar")},
        {"name": "depth1_grantee_must_read", "description": "Non-owner with a depth-1 grant from the owner MUST be permitted to read", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "depth1_grantee_must_read.cedar")},
        {"name": "depth1_grantee_must_write", "description": "Non-owner with a depth-1 grant from the owner MUST be permitted to write", "type": "floor", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "depth1_grantee_must_write.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_read", "description": "User+read+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource"},
        {"name": "liveness_write", "description": "User+write+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Resource"},
        {"name": "liveness_delegate", "description": "User+delegate+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"delegate\"", "resource_type": "Resource"},
    ]
