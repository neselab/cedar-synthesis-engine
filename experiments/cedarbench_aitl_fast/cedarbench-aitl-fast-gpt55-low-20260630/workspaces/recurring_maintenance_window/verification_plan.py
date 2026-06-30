"""Hand-authored verification plan for realworld/recurring_maintenance_window.

Recurring maintenance-window pattern exercising Cedar's datetime/duration
arithmetic. The key insight: Cedar has no modulo on datetime, so the host
application pre-computes the current window boundaries and supplies them
as `windowStart: datetime` and `windowDuration: duration`. The policy
then checks whether `context.now` falls inside
  [windowStart, windowStart.offset(windowDuration))
to decide admission.

Safety properties:
  - Ordinary users are locked out while the system is in its maintenance
    window.
  - Oncall engineers and admins can access at any time.
  - Only admins may perform adminOperation, and only during a window.

Common failure modes:
  - Candidate permits user access during the window.
  - Candidate permits non-admin adminOperation.
  - Candidate permits adminOperation outside the window.
  - Candidate uses `.lessThan()` / `.offset()` wrong, or reverses the
    boundary check.
  - Candidate forgets to grant oncall/admin access through the window.

8 checks total (2 ceilings + 4 floors + 2 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "access_safety",
            "description": (
                "access permitted only when role is oncall/admin OR the "
                "request time is outside the window (context.now < "
                "windowStart OR context.now >= windowStart.offset(windowDuration))"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "System",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },
        {
            "name": "admin_operation_safety",
            "description": (
                "adminOperation permitted only when role is admin AND the "
                "request time is inside the window (windowStart <= now < "
                "windowStart.offset(windowDuration))"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"adminOperation"',
            "resource_type": "System",
            "reference_path": os.path.join(REFS, "admin_operation_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "user_outside_window_access",
            "description": "Ordinary user MUST be able to access when outside the maintenance window",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "user_outside_window_access.cedar"),
        },
        {
            "name": "oncall_anytime_access",
            "description": "Oncall engineer MUST be able to access at any time",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "oncall_anytime_access.cedar"),
        },
        {
            "name": "admin_anytime_access",
            "description": "Admin MUST be able to access at any time",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "admin_anytime_access.cedar"),
        },
        {
            "name": "admin_in_window_operation",
            "description": "Admin MUST be able to perform adminOperation inside the maintenance window",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"adminOperation"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "admin_in_window_operation.cedar"),
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
            "name": "liveness_admin_operation",
            "description": "User+adminOperation+System liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"adminOperation"',
            "resource_type": "System",
        },
    ]
