"""Hand-authored verification plan for realworld/if_then_else_decision_tree.

Incident-response platform whose access rules form a decision tree
keyed on incident severity (and category, for `respond`). The property
under test is that the synthesizer uses Cedar's expression-level
`if X then Y else Z` operator. Most LLMs default to desugaring this
into chained `&&`/`||` clauses, which is logically equivalent but
syntactically distinct from the references.

13 checks total (4 ceilings + 5 floors + 4 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "view_safety",
            "description": (
                "view permitted only when clearanceLevel meets the "
                "severity-tiered threshold (>=4 for sev>=8, >=3 for "
                "sev>=5, >=2 for sev>=3, else >=1)"
            ),
            "type": "implies",
            "principal_type": "Responder",
            "action": 'Action::"view"',
            "resource_type": "Incident",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "respond_safety",
            "description": (
                "respond permitted only when BOTH the severity-tiered "
                "threshold AND the category-tiered threshold are satisfied"
            ),
            "type": "implies",
            "principal_type": "Responder",
            "action": 'Action::"respond"',
            "resource_type": "Incident",
            "reference_path": os.path.join(REFS, "respond_safety.cedar"),
        },
        {
            "name": "escalate_safety",
            "description": (
                "escalate permitted unconditionally when severity < 8; "
                "requires clearanceLevel >= 4 when severity >= 8"
            ),
            "type": "implies",
            "principal_type": "Responder",
            "action": 'Action::"escalate"',
            "resource_type": "Incident",
            "reference_path": os.path.join(REFS, "escalate_safety.cedar"),
        },
        {
            "name": "closeIncident_safety",
            "description": (
                "closeIncident permitted only when clearanceLevel >= 5"
            ),
            "type": "implies",
            "principal_type": "Responder",
            "action": 'Action::"closeIncident"',
            "resource_type": "Incident",
            "reference_path": os.path.join(REFS, "closeIncident_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "low_severity_view",
            "description": (
                "Any Responder MUST be permitted to view an incident "
                "with severity <= 2 (lowest tier requires only "
                "clearanceLevel >= 1)"
            ),
            "type": "floor",
            "principal_type": "Responder",
            "action": 'Action::"view"',
            "resource_type": "Incident",
            "floor_path": os.path.join(REFS, "low_severity_view.cedar"),
        },
        {
            "name": "high_severity_senior_view",
            "description": (
                "A senior Responder (clearanceLevel >= 4) MUST be permitted "
                "to view a high-severity (severity >= 8) incident"
            ),
            "type": "floor",
            "principal_type": "Responder",
            "action": 'Action::"view"',
            "resource_type": "Incident",
            "floor_path": os.path.join(REFS, "high_severity_senior_view.cedar"),
        },
        {
            "name": "low_severity_network_respond",
            "description": (
                "A Responder with clearanceLevel >= 2 MUST be permitted to "
                "respond to a low-severity (severity <= 2) network incident"
            ),
            "type": "floor",
            "principal_type": "Responder",
            "action": 'Action::"respond"',
            "resource_type": "Incident",
            "floor_path": os.path.join(REFS, "low_severity_network_respond.cedar"),
        },
        {
            "name": "low_severity_any_escalate",
            "description": (
                "Any Responder MUST be permitted to escalate an incident "
                "with severity <= 7"
            ),
            "type": "floor",
            "principal_type": "Responder",
            "action": 'Action::"escalate"',
            "resource_type": "Incident",
            "floor_path": os.path.join(REFS, "low_severity_any_escalate.cedar"),
        },
        {
            "name": "senior_close",
            "description": (
                "A Responder with clearanceLevel >= 5 MUST be permitted to "
                "closeIncident on any incident"
            ),
            "type": "floor",
            "principal_type": "Responder",
            "action": 'Action::"closeIncident"',
            "resource_type": "Incident",
            "floor_path": os.path.join(REFS, "senior_close.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "Responder+view+Incident liveness",
            "type": "always-denies-liveness",
            "principal_type": "Responder",
            "action": 'Action::"view"',
            "resource_type": "Incident",
        },
        {
            "name": "liveness_respond",
            "description": "Responder+respond+Incident liveness",
            "type": "always-denies-liveness",
            "principal_type": "Responder",
            "action": 'Action::"respond"',
            "resource_type": "Incident",
        },
        {
            "name": "liveness_escalate",
            "description": "Responder+escalate+Incident liveness",
            "type": "always-denies-liveness",
            "principal_type": "Responder",
            "action": 'Action::"escalate"',
            "resource_type": "Incident",
        },
        {
            "name": "liveness_closeIncident",
            "description": "Responder+closeIncident+Incident liveness",
            "type": "always-denies-liveness",
            "principal_type": "Responder",
            "action": 'Action::"closeIncident"',
            "resource_type": "Incident",
        },
    ]
