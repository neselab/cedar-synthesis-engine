"""Hand-authored verification plan for realworld/incident_response_war_room.

Tiered incident-escalation access for an SRE platform.  Tests:
  - severity-to-clearance mapping (sev1->3, sev2->2, sev3->1) via a
    multi-branch disjunction in one permit rule
  - role-string comparisons for tiered access (oncall < lead < commander)
  - active vs resolved incident gating per action
  - post-mortem log access that intentionally survives resolution

Hunts failure modes:
  - Model collapses the severity-clearance mapping into a single branch
    (e.g. always requires clearanceLevel >= 3)
  - Model forgets the isActive guard on viewDetails or declareResolved
    while correctly adding it on updateStatus
  - Model blocks accessLogs on resolved incidents (over-restrictive)
  - Model permits declareResolved for leads (under-restrictive)
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings --------------------------------------------------
        {
            "name": "viewDetails_safety",
            "description": "viewDetails permitted only on active incidents",
            "type": "implies",
            "principal_type": "Responder",
            "action": 'Action::"viewDetails"',
            "resource_type": "Incident",
            "reference_path": os.path.join(REFS, "viewDetails_safety.cedar"),
        },
        {
            "name": "updateStatus_safety",
            "description": "updateStatus permitted only on active incidents with matching clearance-severity threshold",
            "type": "implies",
            "principal_type": "Responder",
            "action": 'Action::"updateStatus"',
            "resource_type": "Incident",
            "reference_path": os.path.join(REFS, "updateStatus_safety.cedar"),
        },
        {
            "name": "accessLogs_safety",
            "description": "accessLogs permitted only for leads and commanders (any incident state)",
            "type": "implies",
            "principal_type": "Responder",
            "action": 'Action::"accessLogs"',
            "resource_type": "Incident",
            "reference_path": os.path.join(REFS, "accessLogs_safety.cedar"),
        },
        {
            "name": "declareResolved_safety",
            "description": "declareResolved permitted only for commanders on active incidents",
            "type": "implies",
            "principal_type": "Responder",
            "action": 'Action::"declareResolved"',
            "resource_type": "Incident",
            "reference_path": os.path.join(REFS, "declareResolved_safety.cedar"),
        },

        # -- Floors ------------------------------------------------------------
        {
            "name": "floor_viewDetails_active",
            "description": "Any responder MUST be permitted to view an active incident",
            "type": "floor",
            "principal_type": "Responder",
            "action": 'Action::"viewDetails"',
            "resource_type": "Incident",
            "floor_path": os.path.join(REFS, "floor_viewDetails_active.cedar"),
        },
        {
            "name": "floor_updateStatus_sev1",
            "description": "Responder with clearanceLevel >= 3 MUST be permitted to updateStatus on active sev1",
            "type": "floor",
            "principal_type": "Responder",
            "action": 'Action::"updateStatus"',
            "resource_type": "Incident",
            "floor_path": os.path.join(REFS, "floor_updateStatus_sev1.cedar"),
        },
        {
            "name": "floor_updateStatus_sev2",
            "description": "Responder with clearanceLevel >= 2 MUST be permitted to updateStatus on active sev2",
            "type": "floor",
            "principal_type": "Responder",
            "action": 'Action::"updateStatus"',
            "resource_type": "Incident",
            "floor_path": os.path.join(REFS, "floor_updateStatus_sev2.cedar"),
        },
        {
            "name": "floor_accessLogs_lead",
            "description": "Lead MUST be permitted to access logs on any incident",
            "type": "floor",
            "principal_type": "Responder",
            "action": 'Action::"accessLogs"',
            "resource_type": "Incident",
            "floor_path": os.path.join(REFS, "floor_accessLogs_lead.cedar"),
        },
        {
            "name": "floor_declareResolved_commander",
            "description": "Commander MUST be permitted to declareResolved on an active incident",
            "type": "floor",
            "principal_type": "Responder",
            "action": 'Action::"declareResolved"',
            "resource_type": "Incident",
            "floor_path": os.path.join(REFS, "floor_declareResolved_commander.cedar"),
        },

        # -- Liveness ----------------------------------------------------------
        {
            "name": "liveness_viewDetails",
            "description": "Responder+viewDetails+Incident liveness",
            "type": "always-denies-liveness",
            "principal_type": "Responder",
            "action": 'Action::"viewDetails"',
            "resource_type": "Incident",
        },
        {
            "name": "liveness_updateStatus",
            "description": "Responder+updateStatus+Incident liveness",
            "type": "always-denies-liveness",
            "principal_type": "Responder",
            "action": 'Action::"updateStatus"',
            "resource_type": "Incident",
        },
        {
            "name": "liveness_accessLogs",
            "description": "Responder+accessLogs+Incident liveness",
            "type": "always-denies-liveness",
            "principal_type": "Responder",
            "action": 'Action::"accessLogs"',
            "resource_type": "Incident",
        },
        {
            "name": "liveness_declareResolved",
            "description": "Responder+declareResolved+Incident liveness",
            "type": "always-denies-liveness",
            "principal_type": "Responder",
            "action": 'Action::"declareResolved"',
            "resource_type": "Incident",
        },
    ]
