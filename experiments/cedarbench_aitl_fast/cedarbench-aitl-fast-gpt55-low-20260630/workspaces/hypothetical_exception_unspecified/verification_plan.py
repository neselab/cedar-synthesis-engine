"""Hand-authored verification plan for realworld/hypothetical_exception_unspecified.

This scenario tests Phase 1 / synthesizer discipline: the spec uses
hedging language ("Users can NORMALLY view their own profile.
Exceptions are RARE and handled separately by the security team")
which superficially suggests an exception path, but does NOT define
any in-policy attribute or condition for the exceptions.

The correct policy encodes the literal rule:
    permit when principal == resource.owner
with NO extra conditions. A tempted planner / synthesizer that adds
`&& !context.someException` invents an attribute the schema does not
declare and the spec does not authorize.

The ceiling and floor are the SAME literal rule, pinning the bound
range to a single point. Any over-restrictive candidate (one that
adds an invented exception predicate) fails the floor; any
over-permissive candidate (one that drops the owner equality) fails
the ceiling.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "owner_view_ceiling",
            "description": "viewProfile permitted ONLY when principal == resource.owner (no invented exceptions)",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"viewProfile\"",
            "resource_type": "Profile",
            "reference_path": os.path.join(REFS, "owner_view_ceiling.cedar"),
        },
        {
            "name": "owner_view_floor",
            "description": "viewProfile MUST be permitted whenever principal == resource.owner (no invented exclusions)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"viewProfile\"",
            "resource_type": "Profile",
            "floor_path": os.path.join(REFS, "owner_view_floor.cedar"),
        },
        {
            "name": "liveness_view_profile",
            "description": "User+viewProfile+Profile liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"viewProfile\"",
            "resource_type": "Profile",
        },
    ]
