"""Verification plan for ten_level_hierarchy."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {"name": "access_safety", "description": "access only when principal in parentOrg", "type": "implies", "principal_type": "Individual", "action": 'Action::"access"', "resource_type": "Resource", "reference_path": os.path.join(REFS, "access_safety.cedar")},
        {"name": "floor_in_chain_must_access", "description": "in-chain individual must access", "type": "floor", "principal_type": "Individual", "action": 'Action::"access"', "resource_type": "Resource", "floor_path": os.path.join(REFS, "floor_in_chain_must_access.cedar")},
        # NOTE: no liveness check — entity-graph `in` is not symcc-verifiable for liveness (§8.10).
    ]
