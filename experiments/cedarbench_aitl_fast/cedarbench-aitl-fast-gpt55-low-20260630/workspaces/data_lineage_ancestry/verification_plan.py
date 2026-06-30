"""Hand-authored verification plan for realworld/data_lineage_ancestry.

Data lineage ancestry pattern: access to datasets is gated by the
user's clearance relative to the dataset's inherited classification
label (public < internal < restricted). Four actions layer additional
constraints:
  - query:  clearance >= classification
  - derive: clearance >= classification AND department match
  - export: clearance >= classification AND no personal data
  - delete: clearance == restricted AND department match

Tests hierarchical string-enum clearance encoded as explicit
disjunctions, boolean attribute gates, and department-scoped actions.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "query_safety",
            "description": "query permitted only when clearance dominates classification",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"query"',
            "resource_type": "Dataset",
            "reference_path": os.path.join(REFS, "query_safety.cedar"),
        },
        {
            "name": "derive_safety",
            "description": "derive permitted only when clearance dominates classification AND department matches",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"derive"',
            "resource_type": "Dataset",
            "reference_path": os.path.join(REFS, "derive_safety.cedar"),
        },
        {
            "name": "export_safety",
            "description": "export permitted only when clearance dominates classification AND dataset has no personal data",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"export"',
            "resource_type": "Dataset",
            "reference_path": os.path.join(REFS, "export_safety.cedar"),
        },
        {
            "name": "delete_safety",
            "description": "delete permitted only when clearance is restricted AND department matches",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "Dataset",
            "reference_path": os.path.join(REFS, "delete_safety.cedar"),
        },

        # -- Floors ---------------------------------------------------------
        {
            "name": "floor_query_public",
            "description": "any user MUST be able to query a public dataset",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"query"',
            "resource_type": "Dataset",
            "floor_path": os.path.join(REFS, "floor_query_public.cedar"),
        },
        {
            "name": "floor_derive_internal",
            "description": "internal-or-higher user in matching department MUST derive from internal dataset",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"derive"',
            "resource_type": "Dataset",
            "floor_path": os.path.join(REFS, "floor_derive_internal.cedar"),
        },
        {
            "name": "floor_export_internal",
            "description": "internal-or-higher user MUST export internal non-personal-data dataset",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"export"',
            "resource_type": "Dataset",
            "floor_path": os.path.join(REFS, "floor_export_internal.cedar"),
        },
        {
            "name": "floor_delete",
            "description": "restricted-clearance user in matching department MUST delete a dataset",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "Dataset",
            "floor_path": os.path.join(REFS, "floor_delete.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_query",
            "description": "User+query+Dataset liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"query"',
            "resource_type": "Dataset",
        },
        {
            "name": "liveness_derive",
            "description": "User+derive+Dataset liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"derive"',
            "resource_type": "Dataset",
        },
        {
            "name": "liveness_export",
            "description": "User+export+Dataset liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"export"',
            "resource_type": "Dataset",
        },
        {
            "name": "liveness_delete",
            "description": "User+delete+Dataset liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "Dataset",
        },
    ]
