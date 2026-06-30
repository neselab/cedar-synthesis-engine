"""Hand-authored verification plan for realworld/cascading_session_expiry.

Cascading session expiry: the effective expiry of a session is the
EARLIER (the minimum) of its parent's expiry and its own self expiry.
Cedar has no `min` operator; the idiomatic encoding is the conjunction
    context.now < context.session.parentExpiresAt
    && context.now < context.session.selfExpiresAt
which is logically equivalent to
    context.now < min(parentExpiresAt, selfExpiresAt)
or to the explicit if-then-else form.

Failure modes hunted:
  - Candidate uses only one of the two expiries (forgets to cascade).
  - Candidate uses MAX instead of MIN (e.g. an OR instead of an AND).
  - Candidate inverts the comparison and permits expired sessions.

4 checks total (1 ceiling + 2 floors + 1 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling -------------------------------------------------
        {
            "name": "usesession_safety",
            "description": (
                "useSession is permitted only when context.now is strictly "
                "before BOTH parentExpiresAt and selfExpiresAt (equivalently, "
                "before min(parentExpiresAt, selfExpiresAt))"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"useSession"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "usesession_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_parent_is_binding",
            "description": (
                "Concrete probe where parentExpiresAt is the earlier "
                "(binding) expiry and now is before both -- MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"useSession"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_parent_is_binding.cedar"),
        },
        {
            "name": "floor_self_is_binding",
            "description": (
                "Concrete probe where selfExpiresAt is the earlier "
                "(binding) expiry and now is before both -- MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"useSession"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_self_is_binding.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_usesession",
            "description": "User+useSession+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"useSession"',
            "resource_type": "Resource",
        },
    ]
