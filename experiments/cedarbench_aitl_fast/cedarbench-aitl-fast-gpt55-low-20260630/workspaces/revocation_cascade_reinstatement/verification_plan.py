"""Hand-authored verification plan for realworld/revocation_cascade_reinstatement.

Tests parent revocation cascading to derived permissions.

The host application walks the grant chain and pre-computes two
boolean attestations into context (Cedar cannot universally quantify
over Set<...>):
  - accessAuthorized:   every link in the chain is currently active.
  - revocationDetected: at least one link has been revoked.

The Cedar policy composes these with an unconditional owner bypass.

Hunts for the failure modes:
  (a) Forgetting the owner bypass and gating ALL reads on
      accessAuthorized — fails floor_owner_read.
  (b) Forgetting to negate revocationDetected — fails read_safety
      (over-permissive: cascade-revoked grantees pass).
  (c) Conditioning the owner branch on !revocationDetected — fails
      floor_owner_read_under_revocation.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling --------------------------------------------------
        {
            "name": "read_safety",
            "description": (
                "read permitted only when (principal == owner) OR "
                "(accessAuthorized AND NOT revocationDetected)"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "floor_owner_read",
            "description": (
                "Owner MUST be able to read their own resource "
                "(unconditional owner bypass)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_owner_read.cedar"),
        },
        {
            "name": "floor_authorized_grantee_read",
            "description": (
                "Non-owner grantee with accessAuthorized AND NOT "
                "revocationDetected MUST be permitted to read"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "floor_path": os.path.join(
                REFS, "floor_authorized_grantee_read.cedar"
            ),
        },
        {
            "name": "floor_owner_read_under_revocation",
            "description": (
                "Owner MUST read even when revocationDetected == true "
                "(owner is chain root and never cascade-invalidated)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "floor_path": os.path.join(
                REFS, "floor_owner_read_under_revocation.cedar"
            ),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_read",
            "description": "User+read+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Resource",
        },
    ]
