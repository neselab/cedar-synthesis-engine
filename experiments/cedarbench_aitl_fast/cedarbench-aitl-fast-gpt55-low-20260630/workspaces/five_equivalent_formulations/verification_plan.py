"""Hand-authored verification plan for realworld/five_equivalent_formulations.

Tests that the harness accepts ANY of several semantically-equivalent
encodings of one access rule. The rule:

    permit read when (principal.role == "admin") OR (resource.tier == 1)

Cedar admits at least five surface forms for this rule (see policy_spec.md):
disjunction, integer-comparison rewrite, if/then/else, de Morgan negation,
and set-of-one membership. `cedar symcc` should prove all five equivalent
to the canonical ceiling.

If Haiku stalls on this scenario, the bug is most likely in feedback
formatting biasing the model toward a specific surface syntax — i.e. the
harness is implicitly demanding canonical form rather than accepting any
extensionally equivalent program. That would be a regression vs. the
"property-based plans" principle in §5.2.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceiling ────────────────────────────────────────────────
        {
            "name": "read_safety_ceiling",
            "description": "read permitted only when principal.role == \"admin\" OR resource.tier == 1",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "Doc",
            "reference_path": os.path.join(REFS, "read_safety_ceiling.cedar"),
        },

        # ── Floors (corners of the disjunction) ───────────────────────────
        {
            "name": "floor_admin_reads_any_tier",
            "description": "admin User MUST read any Doc",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "Doc",
            "floor_path": os.path.join(REFS, "floor_admin_reads_any_tier.cedar"),
        },
        {
            "name": "floor_anyone_reads_tier1",
            "description": "any User MUST read a tier-1 Doc",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "Doc",
            "floor_path": os.path.join(REFS, "floor_anyone_reads_tier1.cedar"),
        },
        {
            "name": "floor_admin_reads_tier1",
            "description": "admin User MUST read a tier-1 Doc (overlap corner)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "Doc",
            "floor_path": os.path.join(REFS, "floor_admin_reads_tier1.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_read",
            "description": "User+read+Doc liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "Doc",
        },
    ]
