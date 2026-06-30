"""Hand-authored verification plan for realworld/policy_annotations.

Tests Cedar's @id and @description policy annotations alongside
a simple RBAC model (viewer/editor/admin on articles).

The annotations are syntactic — symcc verifies the semantic content
of the rules regardless of whether annotations are present. The spec
requires annotations, so if Haiku omits them, the policy is still
semantically valid but doesn't match the spec's annotation requirement.
(The harness cannot currently enforce annotation presence — that would
be a structural check, not a semantic one. This scenario tests whether
Haiku follows the spec instruction to add annotations.)

Checks:
  - 3 ceilings (read/write/delete safety)
  - 3 floors (viewer reads published, editor writes, admin deletes)
  - 3 liveness
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "read_safety",
            "description": "read permitted only when viewer+published, editor, or admin",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Article",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },
        {
            "name": "write_safety",
            "description": "write permitted only when editor or admin",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"write"',
            "resource_type": "Article",
            "reference_path": os.path.join(REFS, "write_safety.cedar"),
        },
        {
            "name": "delete_safety",
            "description": "delete permitted only when admin",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "Article",
            "reference_path": os.path.join(REFS, "delete_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "floor_viewer_read_published",
            "description": "viewer MUST read published articles",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Article",
            "floor_path": os.path.join(REFS, "floor_viewer_read_published.cedar"),
        },
        {
            "name": "floor_editor_write",
            "description": "editor MUST write any article",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"write"',
            "resource_type": "Article",
            "floor_path": os.path.join(REFS, "floor_editor_write.cedar"),
        },
        {
            "name": "floor_admin_delete",
            "description": "admin MUST delete any article",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "Article",
            "floor_path": os.path.join(REFS, "floor_admin_delete.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_read",
            "description": "at least one read must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Article",
        },
        {
            "name": "liveness_write",
            "description": "at least one write must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"write"',
            "resource_type": "Article",
        },
        {
            "name": "liveness_delete",
            "description": "at least one delete must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "Article",
        },
    ]
