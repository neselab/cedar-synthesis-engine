"""Hand-authored verification plan for realworld/entity_tags_with_hastag.

Tests Cedar's entity tags feature (RFC 0082): `hasTag`/`getTag` on
entities declared with `tags Set<String>`. Tag values are themselves
`Set<String>`, so set operations compose with tag lookups.

This is the first scenario in the benchmark to exercise entity tags.
It is rated hard because:
  - LLMs are largely unaware the feature exists and often hallucinate
    a record-attribute shape.
  - Every getTag read must be guarded by a hasTag check (analogous to
    optional-attribute `has` guards).
  - The negated-hasTag trap mirrors §5.4/§8.3: writing
    `!resource.hasTag("K") || principal.getTag("K")...` fails the
    type-checker; must be restated in positive-guard form.

Checks:
  - 3 ceilings (view/edit/declassify safety)
  - 4 floors (view no-compartments, view with-compartments,
    edit no-compartments, declassify)
  - 3 liveness
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "view_safety",
            "description": "view permitted only when clearance covers required_clearance and (if present) compartments match",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "edit_safety",
            "description": "edit permitted only when view preconditions hold AND edit_authorized tag contains \"true\"",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "edit_safety.cedar"),
        },
        {
            "name": "declassify_safety",
            "description": "declassify permitted only when role tag contains \"declassifier\"",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"declassify"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "declassify_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "floor_view_no_compartments",
            "description": "user with covering clearance MUST view documents that have no compartments_required",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_view_no_compartments.cedar"),
        },
        {
            "name": "floor_view_with_compartments",
            "description": "user with covering clearance AND covering compartments MUST view documents that declare compartments_required",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_view_with_compartments.cedar"),
        },
        {
            "name": "floor_edit_no_compartments",
            "description": "user who satisfies view (no compartments) AND holds edit_authorized=\"true\" MUST edit",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_edit_no_compartments.cedar"),
        },
        {
            "name": "floor_declassify",
            "description": "user whose role tag contains \"declassifier\" MUST declassify",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"declassify"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_declassify.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_view",
            "description": "at least one view must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
        },
        {
            "name": "liveness_edit",
            "description": "at least one edit must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
        },
        {
            "name": "liveness_declassify",
            "description": "at least one declassify must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"declassify"',
            "resource_type": "Document",
        },
    ]
