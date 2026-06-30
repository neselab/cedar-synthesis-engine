"""Hand-authored verification plan for realworld/customer_support_ticket_escalation.

Support ticket escalation with priority-based routing: agents can only
handle tickets up to their maxPriority level. Escalated tickets require
a manager to close. Reassignment is manager-only. Escalation itself is
universally permitted.

Key §8.8 compliance: the floor_close_non_escalated reference includes
resource.isEscalated == false so the floor is jointly satisfiable with
the close_safety ceiling (which gates non-managers on !isEscalated).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "respond_safety",
            "description": "respond permitted only when agent maxPriority >= ticket priority",
            "type": "implies",
            "principal_type": "Agent",
            "action": 'Action::"respond"',
            "resource_type": "Ticket",
            "reference_path": os.path.join(REFS, "respond_safety.cedar"),
        },
        {
            "name": "escalate_safety",
            "description": "escalate permitted unconditionally (any agent, any ticket)",
            "type": "implies",
            "principal_type": "Agent",
            "action": 'Action::"escalate"',
            "resource_type": "Ticket",
            "reference_path": os.path.join(REFS, "escalate_safety.cedar"),
        },
        {
            "name": "close_safety",
            "description": "close permitted only when maxPriority >= priority AND (not escalated OR manager)",
            "type": "implies",
            "principal_type": "Agent",
            "action": 'Action::"close"',
            "resource_type": "Ticket",
            "reference_path": os.path.join(REFS, "close_safety.cedar"),
        },
        {
            "name": "reassign_safety",
            "description": "reassign permitted only when agent role is manager",
            "type": "implies",
            "principal_type": "Agent",
            "action": 'Action::"reassign"',
            "resource_type": "Ticket",
            "reference_path": os.path.join(REFS, "reassign_safety.cedar"),
        },

        # -- Floors ---------------------------------------------------------
        {
            "name": "floor_respond",
            "description": "agent with sufficient maxPriority MUST respond to matching ticket",
            "type": "floor",
            "principal_type": "Agent",
            "action": 'Action::"respond"',
            "resource_type": "Ticket",
            "floor_path": os.path.join(REFS, "floor_respond.cedar"),
        },
        {
            "name": "floor_escalate",
            "description": "any agent MUST be permitted to escalate any ticket",
            "type": "floor",
            "principal_type": "Agent",
            "action": 'Action::"escalate"',
            "resource_type": "Ticket",
            "floor_path": os.path.join(REFS, "floor_escalate.cedar"),
        },
        {
            "name": "floor_close_non_escalated",
            "description": "agent with sufficient maxPriority MUST close non-escalated ticket (§8.8: includes !isEscalated)",
            "type": "floor",
            "principal_type": "Agent",
            "action": 'Action::"close"',
            "resource_type": "Ticket",
            "floor_path": os.path.join(REFS, "floor_close_non_escalated.cedar"),
        },
        {
            "name": "floor_manager_close_escalated",
            "description": "manager with sufficient maxPriority MUST close escalated ticket",
            "type": "floor",
            "principal_type": "Agent",
            "action": 'Action::"close"',
            "resource_type": "Ticket",
            "floor_path": os.path.join(REFS, "floor_manager_close_escalated.cedar"),
        },
        {
            "name": "floor_manager_reassign",
            "description": "manager MUST be permitted to reassign any ticket",
            "type": "floor",
            "principal_type": "Agent",
            "action": 'Action::"reassign"',
            "resource_type": "Ticket",
            "floor_path": os.path.join(REFS, "floor_manager_reassign.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_respond",
            "description": "Agent+respond+Ticket liveness",
            "type": "always-denies-liveness",
            "principal_type": "Agent",
            "action": 'Action::"respond"',
            "resource_type": "Ticket",
        },
        {
            "name": "liveness_escalate",
            "description": "Agent+escalate+Ticket liveness",
            "type": "always-denies-liveness",
            "principal_type": "Agent",
            "action": 'Action::"escalate"',
            "resource_type": "Ticket",
        },
        {
            "name": "liveness_close",
            "description": "Agent+close+Ticket liveness",
            "type": "always-denies-liveness",
            "principal_type": "Agent",
            "action": 'Action::"close"',
            "resource_type": "Ticket",
        },
        {
            "name": "liveness_reassign",
            "description": "Agent+reassign+Ticket liveness",
            "type": "always-denies-liveness",
            "principal_type": "Agent",
            "action": 'Action::"reassign"',
            "resource_type": "Ticket",
        },
    ]
