"""Hand-authored verification plan for realworld/inventory_warehouse_zone.

Warehouse zone-restricted inventory access. Tests:
  - Zone-matching guard (string equality on principal.zone vs resource.currentZone)
  - Wildcard zone ("all") bypass for roaming supervisors
  - Hazardous-item role escalation (supervisor-only for move of hazardous)
  - Action-specific role requirements (dispose = supervisor-only)
  - No forbids -- all restrictions encoded as permit conditions (§8.6 safe)

§8.8 floor consistency: no global forbids exist, so floors only need to
be subsets of the corresponding ceilings. The floor for moving hazardous
items includes role == "supervisor" to satisfy the hazardous escalation
condition in the move ceiling.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) ---------------------------------
        {
            "name": "move_safety",
            "description": "move permitted only when (zone match or zone 'all') AND (non-hazardous or supervisor)",
            "type": "implies",
            "principal_type": "Worker",
            "action": 'Action::"move"',
            "resource_type": "Inventory",
            "reference_path": os.path.join(REFS, "move_safety.cedar"),
        },
        {
            "name": "inspect_safety",
            "description": "inspect permitted only when zone match or zone 'all'",
            "type": "implies",
            "principal_type": "Worker",
            "action": 'Action::"inspect"',
            "resource_type": "Inventory",
            "reference_path": os.path.join(REFS, "inspect_safety.cedar"),
        },
        {
            "name": "dispose_safety",
            "description": "dispose permitted only when supervisor AND (zone match or zone 'all')",
            "type": "implies",
            "principal_type": "Worker",
            "action": 'Action::"dispose"',
            "resource_type": "Inventory",
            "reference_path": os.path.join(REFS, "dispose_safety.cedar"),
        },

        # -- Floors ------------------------------------------------------------
        {
            "name": "floor_handler_move_nonhazardous",
            "description": "Handler in same zone MUST move a non-hazardous item",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"move"',
            "resource_type": "Inventory",
            "floor_path": os.path.join(REFS, "floor_handler_move_nonhazardous.cedar"),
        },
        {
            "name": "floor_supervisor_move_hazardous",
            "description": "Supervisor in same zone MUST move a hazardous item (§8.8: includes role==supervisor to satisfy ceiling)",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"move"',
            "resource_type": "Inventory",
            "floor_path": os.path.join(REFS, "floor_supervisor_move_hazardous.cedar"),
        },
        {
            "name": "floor_handler_inspect",
            "description": "Handler in same zone MUST inspect any item",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"inspect"',
            "resource_type": "Inventory",
            "floor_path": os.path.join(REFS, "floor_handler_inspect.cedar"),
        },
        {
            "name": "floor_supervisor_inspect_all",
            "description": "Supervisor with zone 'all' MUST inspect any item",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"inspect"',
            "resource_type": "Inventory",
            "floor_path": os.path.join(REFS, "floor_supervisor_inspect_all.cedar"),
        },
        {
            "name": "floor_supervisor_dispose",
            "description": "Supervisor in same zone MUST dispose of any item",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"dispose"',
            "resource_type": "Inventory",
            "floor_path": os.path.join(REFS, "floor_supervisor_dispose.cedar"),
        },

        # -- Liveness ----------------------------------------------------------
        {
            "name": "liveness_move",
            "description": "Worker+move+Inventory liveness",
            "type": "always-denies-liveness",
            "principal_type": "Worker",
            "action": 'Action::"move"',
            "resource_type": "Inventory",
        },
        {
            "name": "liveness_inspect",
            "description": "Worker+inspect+Inventory liveness",
            "type": "always-denies-liveness",
            "principal_type": "Worker",
            "action": 'Action::"inspect"',
            "resource_type": "Inventory",
        },
        {
            "name": "liveness_dispose",
            "description": "Worker+dispose+Inventory liveness",
            "type": "always-denies-liveness",
            "principal_type": "Worker",
            "action": 'Action::"dispose"',
            "resource_type": "Inventory",
        },
    ]
