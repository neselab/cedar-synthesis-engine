"""Hand-authored verification plan for realworld/time_of_day_business_hours.

Enterprise time-of-day restriction pattern. The key safety properties:
  - Employees can only access the system during business hours (9-16).
  - Managers and admins can access anytime.
  - Only admins can perform maintenance, and only outside business hours.

The common failure modes this scenario hunts:
  - Candidate permits employee access outside business hours.
  - Candidate permits non-admin maintenance.
  - Candidate permits maintenance during business hours.
  - Candidate forgets to grant manager/admin anytime access.

8 checks total (2 ceilings + 4 floors + 2 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "access_safety",
            "description": "access permitted only when role is manager/admin OR request is during business hours (9 <= currentHour < 17)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "System",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },
        {
            "name": "maintenance_safety",
            "description": "maintenance permitted only when role is admin AND request is outside business hours (currentHour < 9 OR currentHour >= 17)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"maintenance"',
            "resource_type": "System",
            "reference_path": os.path.join(REFS, "maintenance_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "employee_business_hours_access",
            "description": "Employee MUST be able to access the system during business hours",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "employee_business_hours_access.cedar"),
        },
        {
            "name": "manager_anytime_access",
            "description": "Manager MUST be able to access the system at any hour",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "manager_anytime_access.cedar"),
        },
        {
            "name": "admin_anytime_access",
            "description": "Admin MUST be able to access the system at any hour",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "admin_anytime_access.cedar"),
        },
        {
            "name": "admin_offhours_maintenance",
            "description": "Admin MUST be able to perform maintenance outside business hours",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"maintenance"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "admin_offhours_maintenance.cedar"),
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
            "name": "liveness_maintenance",
            "description": "User+maintenance+System liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"maintenance"',
            "resource_type": "System",
        },
    ]
