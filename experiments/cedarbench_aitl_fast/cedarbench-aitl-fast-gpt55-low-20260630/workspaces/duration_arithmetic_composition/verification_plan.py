"""Hand-authored verification plan for realworld/duration_arithmetic_composition.

Multi-step duration arithmetic with explicit sign handling. Cedar does not
support `+` / `-` directly on duration values (the type-checker rejects them
with "expected Long but saw duration"); the supported composition path is
to drop into Long via `duration.toMilliseconds()` and arithmetize on
millisecond counts.

The common failure modes this scenario hunts:
  - Candidate writes `duration("90d") - principal.graceQuotaUsed` (or any
    other duration `+` / `-`), which is a Cedar type error.
  - Candidate composes durations correctly but forgets the sign guards,
    leaving `durationSince` free to return a negative value when
    `now < graceStart` and bypass the budget.
  - Candidate forgets that `graceQuotaUsed` itself is unconstrained at
    the type level and could be (semantically illegitimately) negative,
    again bypassing the budget.
  - Candidate writes the comparison with the wrong operator
    (`<` instead of `<=`, missing the boundary case where
    cumulative == 90d).
  - Candidate adds an unrelated forbid that excludes the fresh-grace
    floor user (graceQuotaUsed == 0d, now == graceStart).

4 checks total: 1 ceiling + 2 floors + 1 liveness.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling -------------------------------------------------
        {
            "name": "access_safety",
            "description": (
                "accessWithGrace permitted only when sign-guarded cumulative "
                "grace consumption (graceQuotaUsed + now.durationSince(graceStart)) "
                "is at most 90d, computed via duration.toMilliseconds()"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"accessWithGrace"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_fresh_grace",
            "description": (
                "A User with graceQuotaUsed == duration(\"0d\") and "
                "context.now == principal.graceStart MUST be permitted "
                "(the simplest inside-budget configuration)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"accessWithGrace"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_fresh_grace.cedar"),
        },
        {
            "name": "floor_well_within_budget",
            "description": (
                "A User satisfying the sign guards whose cumulative consumption "
                "(quotaUsed_ms + (now - graceStart)_ms) is at most 30d_ms "
                "MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"accessWithGrace"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_well_within_budget.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_access",
            "description": "User+accessWithGrace+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"accessWithGrace"',
            "resource_type": "Resource",
        },
    ]
