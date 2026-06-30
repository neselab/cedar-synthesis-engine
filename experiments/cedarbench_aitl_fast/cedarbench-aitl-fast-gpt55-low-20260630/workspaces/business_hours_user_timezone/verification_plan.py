"""Hand-authored verification plan for realworld/business_hours_user_timezone.

Business-hours access enforced against the employee's LOCAL time-of-day,
where the local timezone is supplied per-employee as a Cedar duration
(e.g. duration("-8h") for PST, duration("5h30m") for IST). The host
supplies context.now as a UTC datetime.

Cedar idiom under test:
    context.now.offset(principal.timezoneOffset).toTime()
        >= duration("9h")
    && context.now.offset(principal.timezoneOffset).toTime()
        < duration("17h")

The common failure modes this scenario hunts:
  - Candidate compares context.now directly against duration("9h")
    without going through .offset() and .toTime().
  - Candidate forgets .toTime() and tries to compare a datetime
    against a duration.
  - Candidate forgets to apply principal.timezoneOffset, so the
    business-hours window is checked against UTC rather than local
    time.
  - Candidate uses ISO 8601 duration syntax (e.g. duration("PT9H")),
    which Cedar rejects in favor of Go-style ("9h").
  - Candidate restricts the report action with a time-of-day check
    (over-restriction) when report has no time restriction.
  - Candidate uses an inclusive 17:00 boundary (>= and <=) instead
    of the half-open [9h, 17h) interval.

7 checks total (2 ceilings + 3 floors + 2 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "access_safety",
            "description": "access permitted only when context.now.offset(principal.timezoneOffset).toTime() is in [duration('9h'), duration('17h'))",
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"access"',
            "resource_type": "System",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },
        {
            "name": "report_safety",
            "description": "report permitted only for Employee principal acting on a System resource (no time restriction)",
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"report"',
            "resource_type": "System",
            "reference_path": os.path.join(REFS, "report_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_access_local_business_hours",
            "description": "Any Employee whose local time-of-day (after applying timezoneOffset) is in [duration('9h'), duration('17h')) MUST be permitted to access the System",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"access"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "floor_access_local_business_hours.cedar"),
        },
        {
            "name": "floor_report_anytime",
            "description": "Any Employee MUST be permitted to perform report on a System at any time of day",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"report"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "floor_report_anytime.cedar"),
        },
        {
            "name": "floor_access_pst_concrete",
            "description": "Concrete probe: a PST Employee (timezoneOffset == duration('-8h')) at 2025-03-04T18:00:00Z (= 10:00 local) MUST be permitted to access",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"access"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "floor_access_pst_concrete.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_access",
            "description": "Employee+access+System liveness",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"access"',
            "resource_type": "System",
        },
        {
            "name": "liveness_report",
            "description": "Employee+report+System liveness",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"report"',
            "resource_type": "System",
        },
    ]
