"""Hand-authored verification plan for realworld/missing_edge_case_empty_set.

The deliberately-silent spec says only:
  "A user can view a document by tag when the document has the
   requested tag in its tag set."

Two edge cases the spec does not mention but the planner must encode
as deny (safe default):
  - resource.tags is the empty set
  - context.requestedTag is the empty string

This scenario probes whether the synthesizer infers the safe default
without being explicitly told. The ceiling encodes the two guards
(`!isEmpty()` and `!= ""`) on top of the literal `Set::contains` check.

The floors pin only the documented happy paths ("public", "draft")
and deliberately do NOT include any empty-set or empty-string floor,
because adding one would contradict the implied default-deny semantics
this scenario is designed to test.

Common failure modes this scenario hunts:
  - Naive transcription: `permit when { resource.tags.contains(context.requestedTag) }`
    -- passes the floors but is over-permissive when an upstream bug
    inserts "" into a document's tag set and the client sends "" as
    the requested tag.
  - Forgetting the empty-set guard.
  - Forgetting the empty-string guard.
  - Adding a forbid where a guarded permit suffices (still correct,
    but tests Cedar default-deny understanding).

4 checks total (1 ceiling + 2 floors + 1 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling -------------------------------------------------
        {
            "name": "viewByTag_safety",
            "description": "viewByTag permitted only when resource.tags is non-empty AND context.requestedTag is non-empty AND resource.tags contains context.requestedTag",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"viewByTag"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "viewByTag_safety.cedar"),
        },

        # -- Floors (positive assertions for documented happy paths) -------
        {
            "name": "floor_public_tag",
            "description": "viewByTag with requestedTag == \"public\" on a Document whose tags contains \"public\" MUST be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"viewByTag"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_public_tag.cedar"),
        },
        {
            "name": "floor_draft_tag",
            "description": "viewByTag with requestedTag == \"draft\" on a Document whose tags contains \"draft\" MUST be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"viewByTag"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_draft_tag.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_viewByTag",
            "description": "User+viewByTag+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"viewByTag"',
            "resource_type": "Document",
        },
    ]
