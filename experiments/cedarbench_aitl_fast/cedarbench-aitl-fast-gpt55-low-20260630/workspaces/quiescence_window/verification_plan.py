"""Hand-authored verification plan for realworld/quiescence_window.

Per-user cooldown rate-limiting pattern. The action `performAction` is
permitted only when more than 1 hour has elapsed since the user's
previous successful action (recorded on `principal.lastActionAt`).

Key gotcha (per spec): `durationSince` returns a SIGNED duration, so
candidates must include the explicit sign-guard
`context.now >= principal.lastActionAt` even though the `> 1h` check
is technically sufficient on its own. This defends against clock-skew
bugs and matches the spec's load-bearing requirement.

The common failure modes this scenario hunts:
  - Candidate omits the sign-guard.
  - Candidate uses `>=` instead of `>` (off-by-one on the boundary).
  - Candidate uses ISO-8601 duration syntax (rejected, §8.9).
  - Candidate caps the maximum elapsed window (24h floor catches this).

4 checks total (1 ceiling + 2 floors + 1 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling -------------------------------------------------
        {
            "name": "perform_safety",
            "description": (
                "performAction permitted ONLY when context.now >= "
                "principal.lastActionAt AND "
                "context.now.durationSince(principal.lastActionAt) > "
                "duration(\"1h\")"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"performAction"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "perform_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_two_hour_elapsed",
            "description": (
                "When elapsed >= 2h, performAction MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"performAction"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_two_hour_elapsed.cedar"),
        },
        {
            "name": "floor_day_elapsed",
            "description": (
                "When elapsed >= 24h, performAction MUST be permitted "
                "(sanity bound for large windows)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"performAction"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_day_elapsed.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_perform",
            "description": "User+performAction+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"performAction"',
            "resource_type": "Resource",
        },
    ]
