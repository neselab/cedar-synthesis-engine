"""Hand-authored verification plan for realworld/plateau_landscape_many_equal.

Adversarial plateau-landscape stress test. The semantic rule is "exactly
3 of 5 booleans on the principal must be true" -- in Cedar this expands
to a disjunction over C(5,3) = 10 mutually exclusive 5-tuple cases.

The plan structure (1 ceiling + 5 floors + 1 liveness) is designed so
that many candidate policies have IDENTICAL failure counts but
DIFFERENT failure identities. A candidate that omits a single disjunct
matching one pinned floor passes 4 floors and fails 1; another candidate
that omits a different single disjunct also passes 4 and fails 1, but
on a different floor. There is no local gradient over failure-count
alone -- only the per-check counter-example trace identifies WHICH
disjunct is missing.

The five floors target disjuncts {1, 6, 7, 9, 10} of the 10-disjunct
enumeration (in lexicographic order over the chosen triple). This
covers a representative spread across the C(5,3) lattice (one disjunct
per "shape" of the chosen triple) without making the floor count
explode.

7 checks total (1 ceiling + 5 floors + 1 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling -------------------------------------------------
        {
            "name": "access_safety",
            "description": "access permitted only when EXACTLY 3 of 5 booleans on the principal are true (10-disjunct enumeration)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },

        # -- Floors (each pins one specific 3-of-5 combination) -------------
        {
            "name": "floor_combo_123",
            "description": "User with bool1, bool2, bool3 true and bool4, bool5 false MUST be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_combo_123.cedar"),
        },
        {
            "name": "floor_combo_145",
            "description": "User with bool1, bool4, bool5 true and bool2, bool3 false MUST be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_combo_145.cedar"),
        },
        {
            "name": "floor_combo_234",
            "description": "User with bool2, bool3, bool4 true and bool1, bool5 false MUST be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_combo_234.cedar"),
        },
        {
            "name": "floor_combo_245",
            "description": "User with bool2, bool4, bool5 true and bool1, bool3 false MUST be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_combo_245.cedar"),
        },
        {
            "name": "floor_combo_345",
            "description": "User with bool3, bool4, bool5 true and bool1, bool2 false MUST be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_combo_345.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_access",
            "description": "User+access+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
        },
    ]
