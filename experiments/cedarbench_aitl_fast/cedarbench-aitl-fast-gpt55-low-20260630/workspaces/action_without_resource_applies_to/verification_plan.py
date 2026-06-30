"""Hand-authored verification plan for realworld/action_without_resource_applies_to.

Session-management actions that have no real resource. Cedar's schema language
REQUIRES every action to declare a non-empty `resource:` list -- both
`appliesTo { principal, context }` (omitting resource entirely) and
`resource: []` are rejected by the validator.

The canonical workaround is a sentinel `Session` entity with no attributes,
paired with every login / logout / refreshToken request. Policy conditions
on these actions depend only on `principal`, never on `resource`.

`viewProfile` is the contrasting case -- a normal action whose authorization
DOES depend on the resource (`principal == resource.owner`).

12 checks: 4 ceilings + 4 floors + 4 liveness.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) ---------------------------------
        {
            "name": "login_safety",
            "description": "login permitted for any User on any Session (no preconditions)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"login"',
            "resource_type": "Session",
            "reference_path": os.path.join(REFS, "login_safety.cedar"),
        },
        {
            "name": "logout_safety",
            "description": "logout permitted only when principal.sessionActive",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"logout"',
            "resource_type": "Session",
            "reference_path": os.path.join(REFS, "logout_safety.cedar"),
        },
        {
            "name": "refresh_token_safety",
            "description": "refreshToken permitted only when principal.sessionActive AND principal.role != \"guest\"",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"refreshToken"',
            "resource_type": "Session",
            "reference_path": os.path.join(REFS, "refresh_token_safety.cedar"),
        },
        {
            "name": "view_profile_safety",
            "description": "viewProfile permitted only when principal == resource.owner",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"viewProfile"',
            "resource_type": "Profile",
            "reference_path": os.path.join(REFS, "view_profile_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "any_user_must_login",
            "description": "Any User MUST be permitted to log in",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"login"',
            "resource_type": "Session",
            "floor_path": os.path.join(REFS, "any_user_must_login.cedar"),
        },
        {
            "name": "active_user_must_logout",
            "description": "Any User with sessionActive MUST be permitted to log out",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"logout"',
            "resource_type": "Session",
            "floor_path": os.path.join(REFS, "active_user_must_logout.cedar"),
        },
        {
            "name": "active_nonguest_must_refresh",
            "description": "Any active non-guest User MUST be permitted to refresh their token",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"refreshToken"',
            "resource_type": "Session",
            "floor_path": os.path.join(REFS, "active_nonguest_must_refresh.cedar"),
        },
        {
            "name": "owner_must_view_profile",
            "description": "The profile owner MUST be permitted to view their own profile",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"viewProfile"',
            "resource_type": "Profile",
            "floor_path": os.path.join(REFS, "owner_must_view_profile.cedar"),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_login",
            "description": "User+login+Session liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"login"',
            "resource_type": "Session",
        },
        {
            "name": "liveness_logout",
            "description": "User+logout+Session liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"logout"',
            "resource_type": "Session",
        },
        {
            "name": "liveness_refresh_token",
            "description": "User+refreshToken+Session liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"refreshToken"',
            "resource_type": "Session",
        },
        {
            "name": "liveness_view_profile",
            "description": "User+viewProfile+Profile liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"viewProfile"',
            "resource_type": "Profile",
        },
    ]
