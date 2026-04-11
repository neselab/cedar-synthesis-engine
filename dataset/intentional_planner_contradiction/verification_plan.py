"""Hand-authored verification plan for realworld/intentional_planner_contradiction.

This scenario is deliberately constructed to stress-test the §8.8
floor-bound consistency rule. The "author can read their own post"
requirement and the "blocked users cannot read" forbid rule interact
in a corner case (self-blocking), and a naive planner that writes
`permit when principal == resource.author` as the author floor would
produce jointly unsatisfiable bounds when combined with the blocking
ceiling.

As a careful planner following §8.8, I write the author floor with
an explicit `!(principal in principal.blocked)` exclusion — making
the bounds jointly satisfiable by construction. The scenario then
verifies that Haiku can converge on the resulting policy.

If this scenario converges, it confirms the §8.8 rule works. If it
stalls, the rule needs strengthening.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "read_safety",
            "description": "readPost permitted only when neither direction of the mutual-block holds",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"readPost\"",
            "resource_type": "Post",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },
        {
            "name": "author_must_read_not_self_blocked",
            "description": "Author MUST read their own post UNLESS self-blocked (§8.8 exclusion)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"readPost\"",
            "resource_type": "Post",
            "floor_path": os.path.join(REFS, "author_must_read_not_self_blocked.cedar"),
        },
        {
            "name": "non_blocked_reader_must_read",
            "description": "Any non-blocked User MUST read any Post",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"readPost\"",
            "resource_type": "Post",
            "floor_path": os.path.join(REFS, "non_blocked_reader_must_read.cedar"),
        },
        {
            "name": "liveness_read_post",
            "description": "User+readPost+Post liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"readPost\"",
            "resource_type": "Post",
        },
    ]
