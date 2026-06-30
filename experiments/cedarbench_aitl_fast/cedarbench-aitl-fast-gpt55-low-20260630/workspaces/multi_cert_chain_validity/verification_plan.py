"""Hand-authored verification plan for realworld/multi_cert_chain_validity.

PKI three-way interval intersection. The accessSecure action requires that
ALL THREE certificate validity windows (user cert, org cert, CA cert)
contain context.now simultaneously. This is a six-comparison conjunction
where the easy mistake is reversing the direction of one comparison
(>= vs <=) or confusing validFrom with validUntil.

The common failure modes this scenario hunts:
  - Candidate reverses one or more validFrom/validUntil comparisons.
  - Candidate forgets one of the three certificates entirely.
  - Candidate substitutes OR for AND, permitting access when only one
    or two certs are valid.
  - Candidate over-restricts (e.g., adds a strict inequality where the
    spec allows equality on the boundary).

4 checks total (1 ceiling + 2 floors + 1 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling -------------------------------------------------
        {
            "name": "access_safety",
            "description": (
                "accessSecure permitted only when all three cert chains "
                "(user, org, CA) are simultaneously valid at context.now"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"accessSecure"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_all_certs_valid_must_permit",
            "description": (
                "When all three cert chains are simultaneously valid at "
                "context.now, accessSecure MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"accessSecure"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_all_certs_valid_must_permit.cedar"),
        },
        {
            "name": "floor_strict_interior_must_permit",
            "description": (
                "When context.now is in the strict interior of every cert "
                "validity window, accessSecure MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"accessSecure"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_strict_interior_must_permit.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_access_secure",
            "description": "User+accessSecure+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"accessSecure"',
            "resource_type": "Resource",
        },
    ]
