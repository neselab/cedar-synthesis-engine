"""Hand-authored verification plan for realworld/quorum_attestation.

3-of-5 emergency override quorum. Tests:
  - Threshold encoded WITHOUT .size() (Cedar has no such operator) by
    enumerating C(5,3) = 10 quorum subsets and checking each via
    .containsAll(...) on a context.attesters set.
  - Eligible-approver gating on executeEmergency.
  - Open-to-all-Approvers viewing.

Failure modes the harness will hunt:
  1. Using .contains on a single approver instead of .containsAll on a
     3-element subset (under-permits — execute floors fail).
  2. Using .containsAny across the full eligible set (over-permits — a
     single attester would satisfy execute_safety, fails ceiling).
  3. Omitting some of the 10 subsets (under-permits specific quorums
     — e.g. dropping {s3,s4,s5} fails execute_quorum_345_must_permit;
     dropping {s2,s4,s5} fails execute_quorum_245_must_permit).
  4. Failing to gate executeEmergency on principal eligibility — any
     Approver could trigger an override, fails execute_safety ceiling.
  5. Gating viewEmergency on eligibility (under-permits — fails
     view_must_permit floor).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) --------------------------------
        {
            "name": "execute_safety",
            "description": (
                "executeEmergency permitted only when principal is one of "
                "the 5 eligible approvers AND context.attesters contains "
                "at least one 3-of-5 subset (10 disjuncts via containsAll)"
            ),
            "type": "implies",
            "principal_type": "Approver",
            "action": 'Action::"executeEmergency"',
            "resource_type": "EmergencyAction",
            "reference_path": os.path.join(REFS, "execute_safety.cedar"),
        },
        {
            "name": "view_safety",
            "description": (
                "viewEmergency permitted only for Approver principals "
                "(schema-trivial upper bound)"
            ),
            "type": "implies",
            "principal_type": "Approver",
            "action": 'Action::"viewEmergency"',
            "resource_type": "EmergencyAction",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "execute_quorum_123_must_permit",
            "description": (
                "When attesters contains {s1,s2,s3}, an eligible approver "
                "MUST be permitted to executeEmergency"
            ),
            "type": "floor",
            "principal_type": "Approver",
            "action": 'Action::"executeEmergency"',
            "resource_type": "EmergencyAction",
            "floor_path": os.path.join(
                REFS, "execute_quorum_123_must_permit.cedar"
            ),
        },
        {
            "name": "execute_quorum_345_must_permit",
            "description": (
                "When attesters contains {s3,s4,s5} (the 'last' subset, "
                "common omission target), an eligible approver MUST be "
                "permitted to executeEmergency"
            ),
            "type": "floor",
            "principal_type": "Approver",
            "action": 'Action::"executeEmergency"',
            "resource_type": "EmergencyAction",
            "floor_path": os.path.join(
                REFS, "execute_quorum_345_must_permit.cedar"
            ),
        },
        {
            "name": "execute_quorum_245_must_permit",
            "description": (
                "When attesters contains {s2,s4,s5} (a non-adjacent "
                "subset, catches contiguous-only enumerations), an "
                "eligible approver MUST be permitted to executeEmergency"
            ),
            "type": "floor",
            "principal_type": "Approver",
            "action": 'Action::"executeEmergency"',
            "resource_type": "EmergencyAction",
            "floor_path": os.path.join(
                REFS, "execute_quorum_245_must_permit.cedar"
            ),
        },
        {
            "name": "view_must_permit",
            "description": (
                "Any Approver MUST be permitted to viewEmergency"
            ),
            "type": "floor",
            "principal_type": "Approver",
            "action": 'Action::"viewEmergency"',
            "resource_type": "EmergencyAction",
            "floor_path": os.path.join(REFS, "view_must_permit.cedar"),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_execute",
            "description": "Approver+executeEmergency+EmergencyAction liveness",
            "type": "always-denies-liveness",
            "principal_type": "Approver",
            "action": 'Action::"executeEmergency"',
            "resource_type": "EmergencyAction",
        },
        {
            "name": "liveness_view",
            "description": "Approver+viewEmergency+EmergencyAction liveness",
            "type": "always-denies-liveness",
            "principal_type": "Approver",
            "action": 'Action::"viewEmergency"',
            "resource_type": "EmergencyAction",
        },
    ]
