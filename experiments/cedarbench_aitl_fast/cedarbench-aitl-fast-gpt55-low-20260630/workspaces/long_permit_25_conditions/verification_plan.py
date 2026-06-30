"""Hand-authored verification plan for realworld/long_permit_25_conditions.

Stress-tests synthesis of a single permit policy whose `when` clause is a
long (25-clause) AND-chained conjunction over principal/resource/context
attributes. Models real enterprise audit-heavy access control patterns
where regulators stack many independent gates onto a single decision.

Hunts the failure modes:
  - Dropping any of the 25 clauses (especially the redundant trio
    16/17/18 sanity bounds, or the duplicated clauses 21 and 25).
  - Inverting the polarity of `requiresNda`/`complianceFlag` so the
    floor with `requiresNda=false` is denied.
  - Swapping `<` for `<=` on the MFA freshness duration check.
  - Using ISO-8601 duration syntax (§8.9 trap).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling ---------------------------------------------------
        {
            "name": "access_safety",
            "description": (
                "accessSensitive permitted only when all 25 AND-chained "
                "conditions hold (employee role, fresh MFA, clearance, "
                "dept match, not archived, not contractor, compliance, "
                "background check, VPN, low risk, no incident, location, "
                "classification gates, clearance bounds, NDA gating, "
                "compliance flag gating, non-empty dept strings)"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"accessSensitive"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "floor_clean_employee_must_permit",
            "description": (
                "A fully-credentialed employee on a confidential resource "
                "with NDA + compliance flags satisfied MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"accessSensitive"',
            "resource_type": "Resource",
            "floor_path": os.path.join(
                REFS, "floor_clean_employee_must_permit.cedar"
            ),
        },
        {
            "name": "floor_no_nda_internal_must_permit",
            "description": (
                "An employee on an internal resource where requiresNda=false "
                "and complianceFlag=false MUST be permitted even without "
                "principal NDA — polarity check on requiresNda"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"accessSensitive"',
            "resource_type": "Resource",
            "floor_path": os.path.join(
                REFS, "floor_no_nda_internal_must_permit.cedar"
            ),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_access",
            "description": "User+accessSensitive+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"accessSensitive"',
            "resource_type": "Resource",
        },
    ]
