"""Hand-authored verification plan for realworld/inverted_default_permit.

Public-by-default content with an explicit denylist. Tests:
  - Inversion of Cedar's natural deny-by-default model
  - Set<String> membership via .contains() on String, not Entity
  - Single broad permit guarded by a negated containment check

Hunts failure modes:
  - Planner falls back to a deny-by-default shape that requires some
    positive condition (auth check, role, allowlist) the spec does not
    permit. Such a candidate fails the floor for non-banned users.
  - Planner inverts the contains check (forgets the negation) and ends up
    permitting only banned users.
  - Planner adds an unwarranted "principal must exist" or "id must be
    non-empty" guard that breaks the empty-denylist floor.
  - Planner uses .containsAny / .containsAll instead of .contains for a
    scalar membership check.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling -------------------------------------------------
        {
            "name": "read_safety",
            "description": (
                "read permitted only when principal.id is NOT in "
                "resource.bannedReaders"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "PublicArticle",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },

        # -- Floors ---------------------------------------------------------
        {
            "name": "non_banned_user_must_read",
            "description": (
                "A user whose id is NOT in bannedReaders MUST be permitted "
                "to read (core public-by-default guarantee)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "PublicArticle",
            "floor_path": os.path.join(REFS, "non_banned_user_must_read.cedar"),
        },
        {
            "name": "empty_denylist_must_read",
            "description": (
                "When bannedReaders is empty, ANY user MUST be permitted "
                "to read (catches candidates that add unwarranted positive "
                "conditions)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "PublicArticle",
            "floor_path": os.path.join(REFS, "empty_denylist_must_read.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_read",
            "description": "User+read+PublicArticle liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "PublicArticle",
        },
    ]
