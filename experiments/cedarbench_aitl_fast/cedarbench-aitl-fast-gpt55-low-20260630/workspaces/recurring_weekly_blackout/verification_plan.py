"""Hand-authored verification plan for realworld/recurring_weekly_blackout.

Recurring weekly blackout windows enforced via host-supplied boolean
attestation. The host application is responsible for computing whether
the current moment is inside a blackout (Cedar has no modulo or
weekday/time-of-day operator), and the policy routes principals
based on that boolean plus their role.

Common failure modes this scenario hunts:
  - Candidate permits ordinary `user` role to access during a blackout.
  - Candidate permits any non-oncall principal to use `emergencyAccess`.
  - Candidate permits `emergencyAccess` outside a blackout window.
  - Candidate forgets the inverted gating on `emergencyAccess` (it is
    valid ONLY during a blackout, not all the time).
  - Candidate forgets to grant oncall the routine `access` action
    during a blackout.

7 checks total (2 ceilings + 3 floors + 2 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "access_safety",
            "description": "access permitted only when role is oncall OR not in blackout window",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "System",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },
        {
            "name": "emergency_safety",
            "description": "emergencyAccess permitted only when role is oncall AND in blackout window",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"emergencyAccess"',
            "resource_type": "System",
            "reference_path": os.path.join(REFS, "emergency_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "user_access_outside_blackout",
            "description": "An ordinary user MUST be able to access the system when not in a blackout",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "user_access_outside_blackout.cedar"),
        },
        {
            "name": "oncall_access_anytime",
            "description": "An oncall user MUST be able to access the system at any time",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "oncall_access_anytime.cedar"),
        },
        {
            "name": "oncall_emergency_during_blackout",
            "description": "An oncall user MUST be able to perform emergencyAccess during a blackout",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"emergencyAccess"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "oncall_emergency_during_blackout.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_access",
            "description": "User+access+System liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "System",
        },
        {
            "name": "liveness_emergency",
            "description": "User+emergencyAccess+System liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"emergencyAccess"',
            "resource_type": "System",
        },
    ]
