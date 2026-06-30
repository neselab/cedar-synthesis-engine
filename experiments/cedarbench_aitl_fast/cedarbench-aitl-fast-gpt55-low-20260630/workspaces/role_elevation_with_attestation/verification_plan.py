"""Hand-authored verification plan for realworld/role_elevation_with_attestation.

Temporary role elevation with justification attestation. Tests:
  - Optional context attribute (elevationJustification) with mandatory
    has-guard before any read (§8.3 negated-has trap shape).
  - Non-empty string attestation: empty string "" is NOT a valid
    justification. Encoded as `!= ""` (or equivalently `like "?*"`).
  - Manager standing-authority bypass: managers do not need elevation.
  - Conjunction of role + grant flag + context presence + non-empty
    string check on the elevation path.

Hunts for the failure modes where the model:
  (a) omits the has-guard before reading context.elevationJustification,
  (b) accepts elevationGranted alone without requiring a justification,
  (c) treats an empty string as a valid attestation,
  (d) requires elevation/justification of managers (breaks the manager
      standing-authority floor).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) --------------------------------
        {
            "name": "accessNormal_safety",
            "description": (
                "accessNormal permitted only when baseRole is one of "
                "user/lead/manager"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"accessNormal"',
            "resource_type": "SensitiveResource",
            "reference_path": os.path.join(REFS, "accessNormal_safety.cedar"),
        },
        {
            "name": "accessSensitive_safety",
            "description": (
                "accessSensitive permitted only when manager OR "
                "(user/lead AND elevationGranted AND non-empty "
                "elevationJustification)"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"accessSensitive"',
            "resource_type": "SensitiveResource",
            "reference_path": os.path.join(
                REFS, "accessSensitive_safety.cedar"
            ),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "accessNormal_user_floor",
            "description": (
                "A baseRole 'user' MUST be permitted accessNormal"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"accessNormal"',
            "resource_type": "SensitiveResource",
            "floor_path": os.path.join(REFS, "accessNormal_user_floor.cedar"),
        },
        {
            "name": "accessSensitive_manager_floor",
            "description": (
                "A baseRole 'manager' MUST be permitted accessSensitive "
                "without elevation/justification (standing authority)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"accessSensitive"',
            "resource_type": "SensitiveResource",
            "floor_path": os.path.join(
                REFS, "accessSensitive_manager_floor.cedar"
            ),
        },
        {
            "name": "accessSensitive_elevated_user_floor",
            "description": (
                "A baseRole 'user' with elevationGranted=true and a "
                "non-empty elevationJustification MUST be permitted "
                "accessSensitive"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"accessSensitive"',
            "resource_type": "SensitiveResource",
            "floor_path": os.path.join(
                REFS, "accessSensitive_elevated_user_floor.cedar"
            ),
        },
        {
            "name": "accessSensitive_elevated_lead_floor",
            "description": (
                "A baseRole 'lead' with elevationGranted=true and a "
                "non-empty elevationJustification MUST be permitted "
                "accessSensitive"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"accessSensitive"',
            "resource_type": "SensitiveResource",
            "floor_path": os.path.join(
                REFS, "accessSensitive_elevated_lead_floor.cedar"
            ),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_accessNormal",
            "description": "User+accessNormal+SensitiveResource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"accessNormal"',
            "resource_type": "SensitiveResource",
        },
        {
            "name": "liveness_accessSensitive",
            "description": "User+accessSensitive+SensitiveResource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"accessSensitive"',
            "resource_type": "SensitiveResource",
        },
    ]
