"""Hand-authored verification plan for realworld/feature_flag_rollout.

Feature-flag gradual rollout access control. Tests:
  - Boolean attribute gating (isEnabled)
  - Numeric comparison for percentage-based rollout (rolloutBucket < rolloutPercentage)
  - String-based role override (beta_tester, admin bypass rollout gate)
  - Three-tier action hierarchy (use < preview < configure)

Hunts failure modes:
  - Policies that forget the isEnabled guard on use
  - Policies that use <= instead of < for the rollout comparison
  - Policies that collapse preview and use into one rule and leak the
    isEnabled requirement into preview
  - Policies that give beta_testers configure access
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "use_safety",
            "description": (
                "use permitted only when isEnabled AND "
                "(role == beta_tester OR role == admin OR "
                "rolloutBucket < rolloutPercentage)"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"use"',
            "resource_type": "Feature",
            "reference_path": os.path.join(REFS, "use_safety.cedar"),
        },
        {
            "name": "preview_safety",
            "description": "preview permitted only when role is beta_tester or admin",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"preview"',
            "resource_type": "Feature",
            "reference_path": os.path.join(REFS, "preview_safety.cedar"),
        },
        {
            "name": "configure_safety",
            "description": "configure permitted only when role is admin",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"configure"',
            "resource_type": "Feature",
            "reference_path": os.path.join(REFS, "configure_safety.cedar"),
        },

        # -- Floors ---------------------------------------------------------
        {
            "name": "beta_tester_must_use",
            "description": "Beta tester MUST be permitted to use an enabled feature",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"use"',
            "resource_type": "Feature",
            "floor_path": os.path.join(REFS, "beta_tester_must_use.cedar"),
        },
        {
            "name": "rolled_in_user_must_use",
            "description": (
                "User with rolloutBucket < rolloutPercentage MUST be "
                "permitted to use an enabled feature"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"use"',
            "resource_type": "Feature",
            "floor_path": os.path.join(REFS, "rolled_in_user_must_use.cedar"),
        },
        {
            "name": "beta_tester_must_preview",
            "description": "Beta tester MUST be permitted to preview any feature",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"preview"',
            "resource_type": "Feature",
            "floor_path": os.path.join(REFS, "beta_tester_must_preview.cedar"),
        },
        {
            "name": "admin_must_configure",
            "description": "Admin MUST be permitted to configure any feature",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"configure"',
            "resource_type": "Feature",
            "floor_path": os.path.join(REFS, "admin_must_configure.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_use",
            "description": "User+use+Feature liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"use"',
            "resource_type": "Feature",
        },
        {
            "name": "liveness_preview",
            "description": "User+preview+Feature liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"preview"',
            "resource_type": "Feature",
        },
        {
            "name": "liveness_configure",
            "description": "User+configure+Feature liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"configure"',
            "resource_type": "Feature",
        },
    ]
