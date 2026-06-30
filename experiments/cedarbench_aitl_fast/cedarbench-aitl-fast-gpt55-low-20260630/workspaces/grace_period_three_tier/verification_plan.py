"""Hand-authored verification plan for realworld/grace_period_three_tier.

TLS-certificate lifecycle access control. The certificate's `certExpiresAt`
attribute partitions the timeline into four contiguous tiers, and each
tier permits a different action (or none, in tier 4):

  Tier 1 — Pre-warning  (now < certExpiresAt - 7d):   `connect`
  Tier 2 — Warning      ([certExpiresAt-7d, certExpiresAt)): `connectWithWarning`
  Tier 3 — Grace        ([certExpiresAt, certExpiresAt+30d)): `connectInGrace`
  Tier 4 — After grace  (now >= certExpiresAt + 30d):  all denied

The common failure modes this scenario hunts:
  - Candidate uses `>` where it should use `>=` (tier-boundary off-by-one).
  - Candidate writes ISO 8601 duration literals like `duration("PT24H")`
    or `duration("P30D")`; Cedar requires Go-style `"30d"`. (See §8.9.)
  - Candidate forgets `.offset(duration(...))` and tries to subtract a
    duration from a datetime directly.
  - Candidate cuts the grace window short (e.g. encodes 7d grace instead
    of 30d) — caught by `floor_connect_in_grace_late`.
  - Candidate permits `connect` in tiers 2/3 (still has cert lifetime
    semantics in mind) — caught by `connect_safety` ceiling.
  - Candidate permits any connect action in tier 4 — caught by all three
    ceilings, since none of them admit `now >= certExpiresAt + 30d`.

10 checks total (3 ceilings + 4 floors + 3 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "connect_safety",
            "description": "connect permitted only when context.now < principal.certExpiresAt - 7d (tier 1 only)",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": 'Action::"connect"',
            "resource_type": "Service",
            "reference_path": os.path.join(REFS, "connect_safety.cedar"),
        },
        {
            "name": "connect_with_warning_safety",
            "description": "connectWithWarning permitted only in [certExpiresAt - 7d, certExpiresAt) (tier 2 only)",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": 'Action::"connectWithWarning"',
            "resource_type": "Service",
            "reference_path": os.path.join(REFS, "connect_with_warning_safety.cedar"),
        },
        {
            "name": "connect_in_grace_safety",
            "description": "connectInGrace permitted only in [certExpiresAt, certExpiresAt + 30d) (tier 3 only)",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": 'Action::"connectInGrace"',
            "resource_type": "Service",
            "reference_path": os.path.join(REFS, "connect_in_grace_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_connect_pre_warning",
            "description": "Subscriber MUST be able to connect when more than 7 days remain on the cert (tier 1)",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": 'Action::"connect"',
            "resource_type": "Service",
            "floor_path": os.path.join(REFS, "floor_connect_pre_warning.cedar"),
        },
        {
            "name": "floor_connect_with_warning_window",
            "description": "Subscriber MUST be able to connectWithWarning during the 7-day warning window (tier 2)",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": 'Action::"connectWithWarning"',
            "resource_type": "Service",
            "floor_path": os.path.join(REFS, "floor_connect_with_warning_window.cedar"),
        },
        {
            "name": "floor_connect_in_grace_early",
            "description": "Subscriber MUST be able to connectInGrace in the first 7 days after expiry (early tier 3)",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": 'Action::"connectInGrace"',
            "resource_type": "Service",
            "floor_path": os.path.join(REFS, "floor_connect_in_grace_early.cedar"),
        },
        {
            "name": "floor_connect_in_grace_late",
            "description": "Subscriber MUST be able to connectInGrace 7 to 30 days after expiry (late tier 3)",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": 'Action::"connectInGrace"',
            "resource_type": "Service",
            "floor_path": os.path.join(REFS, "floor_connect_in_grace_late.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_connect",
            "description": "Subscriber+connect+Service liveness",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": 'Action::"connect"',
            "resource_type": "Service",
        },
        {
            "name": "liveness_connect_with_warning",
            "description": "Subscriber+connectWithWarning+Service liveness",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": 'Action::"connectWithWarning"',
            "resource_type": "Service",
        },
        {
            "name": "liveness_connect_in_grace",
            "description": "Subscriber+connectInGrace+Service liveness",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": 'Action::"connectInGrace"',
            "resource_type": "Service",
        },
    ]
