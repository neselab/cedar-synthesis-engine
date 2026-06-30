"""Hand-authored verification plan for realworld/delegation_chain_expiry_dual.

Tests two-hop time-bounded delegation:
  - Two optional context attributes (`firstGrant?`, `secondGrant?`)
    each requiring `has` guards before any read
  - Window intersection semantics (both windows must currently be open
    for the chain to authorize)
  - Chain-of-trust continuity check
    (`firstGrant.delegatee == secondGrant.delegator`)
  - Owner fallback path (no grants needed)

Hunts failure modes:
  - Missing `has` guard on either grant (§8.3 negated-`has` trap)
  - Omitted chain-continuity check (delegator-forgery vulnerability)
  - Boundary errors on window endpoints (`==` instead of `<=`/`>=`)
  - Collapsing single-hop and two-hop into one permit and losing
    the chain-of-trust requirement
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "read_safety", "description": "read permitted only when owner OR active single-hop OR active two-hop chain", "type": "implies", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "write_safety", "description": "write permitted only when owner OR active single-hop OR active two-hop chain", "type": "implies", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "write_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "owner_must_read", "description": "Owner MUST be permitted to read", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "owner_must_read.cedar")},
        {"name": "single_hop_must_permit", "description": "Non-owner with active single-hop grant MUST be permitted to read", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "single_hop_must_permit.cedar")},
        {"name": "two_hop_chain_must_permit", "description": "Non-owner at end of continuous two-hop chain with both windows open MUST be permitted to write", "type": "floor", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "two_hop_chain_must_permit.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_read", "description": "User+read+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource"},
        {"name": "liveness_write", "description": "User+write+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"write\"", "resource_type": "Resource"},
    ]
