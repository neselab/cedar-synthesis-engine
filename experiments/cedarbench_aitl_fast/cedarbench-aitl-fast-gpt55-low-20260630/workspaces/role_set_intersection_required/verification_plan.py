"""Hand-authored verification plan for realworld/role_set_intersection_required.

Tests the "must hold ALL of a set of roles/certs" intersection requirement
via Cedar's `.containsAll()` set operation. Adversarial against the much
more common "any of" disjunction reflex (`containsAny`, OR-chains over
expected names).

Checks:
  - 2 ceilings (view safety, handle safety)
  - 3 floors (view-any-worker, handle full-cert, handle empty-required)
  - 2 liveness (view, handle)
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "view_safety",
            "description": "view permitted to any worker on any material",
            "type": "implies",
            "principal_type": "Worker",
            "action": 'Action::"view"',
            "resource_type": "Material",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "handle_safety",
            "description": "handle permitted only when worker certifications "
                           "containsAll resource requiredCerts (intersection req)",
            "type": "implies",
            "principal_type": "Worker",
            "action": 'Action::"handle"',
            "resource_type": "Material",
            "reference_path": os.path.join(REFS, "handle_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "floor_view_any_worker",
            "description": "any worker MUST be able to view any material",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"view"',
            "resource_type": "Material",
            "floor_path": os.path.join(REFS, "floor_view_any_worker.cedar"),
        },
        {
            "name": "floor_handle_full_certs",
            "description": "worker holding all required certs MUST handle",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"handle"',
            "resource_type": "Material",
            "floor_path": os.path.join(REFS, "floor_handle_full_certs.cedar"),
        },
        {
            "name": "floor_handle_empty_required",
            "description": "material with empty requiredCerts MUST be handleable "
                           "by any worker (containsAll over empty set is true)",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"handle"',
            "resource_type": "Material",
            "floor_path": os.path.join(REFS, "floor_handle_empty_required.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_view",
            "description": "at least one view must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "Worker",
            "action": 'Action::"view"',
            "resource_type": "Material",
        },
        {
            "name": "liveness_handle",
            "description": "at least one handle must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "Worker",
            "action": 'Action::"handle"',
            "resource_type": "Material",
        },
    ]
