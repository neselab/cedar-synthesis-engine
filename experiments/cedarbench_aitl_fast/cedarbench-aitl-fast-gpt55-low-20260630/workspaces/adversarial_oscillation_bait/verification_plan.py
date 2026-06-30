"""Hand-authored verification plan for realworld/adversarial_oscillation_bait.

This scenario is engineered to maximize fix-A-break-B oscillation.
Each of the four ceiling disjuncts is matched by exactly one floor,
and the floors are constructed so that the naive fix to one will
break another:

  - FLOOR_ADMIN     ↔ ceiling clause 1 (role == "admin")
  - FLOOR_OWNER     ↔ ceiling clause 2 (owner with MFA-on-confidential)
  - FLOOR_USER_INTERNAL ↔ ceiling clause 3 (user, !contractor, !confidential)
  - FLOOR_CONTRACTOR_MFA_CONFIDENTIAL ↔ ceiling clause 4

The same five-rule structure is replicated across `read`, `write`,
and `delete`, giving the synthesizer three parallel oscillation
surfaces. A converged candidate must combine four narrowly-scoped
permits per action with no global forbid that violates §8.6
(role-intersection trap).

Plan totals: 3 ceilings + 12 floors + 3 liveness = 18 checks.

Stresses simultaneously:
  §8.1 directional feedback — without it, "fix made the floor pass
       but broke the ceiling in cell X" is invisible to the LLM.
  §8.2 hash-based oscillation detection — likely to revisit prior
       candidates without precise localization.
  §8.6 role-intersection trap — naive `forbid when isContractor &&
       classification == "confidential"` breaks the contractor-MFA
       floor.
  §8.8 floor-bound consistency — the owner floor includes the
       MFA-on-confidential carve-out so the bounds are jointly
       satisfiable.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    checks = []

    # ── Safety ceilings (one per action) ──────────────────────
    for action in ("read", "write", "delete"):
        checks.append({
            "name": f"{action}_safety",
            "description": (
                f"{action} permitted only via the four-disjunct ceiling "
                "(admin / owner-with-MFA-on-confidential / user-non-contractor"
                "-non-confidential / contractor-MFA-confidential)"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": f"Action::\"{action}\"",
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, f"{action}_safety.cedar"),
        })

    # ── Floors (four per action) ──────────────────────────────
    for action in ("read", "write", "delete"):
        checks.append({
            "name": f"floor_admin_{action}",
            "description": f"admin MUST be permitted to {action} any Resource",
            "type": "floor",
            "principal_type": "User",
            "action": f"Action::\"{action}\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, f"floor_admin_{action}.cedar"),
        })
        checks.append({
            "name": f"floor_owner_{action}",
            "description": (
                f"owner MUST be permitted to {action} their Resource "
                "(§8.8 carve-out: MFA required when classification == confidential "
                "and role != admin)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": f"Action::\"{action}\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, f"floor_owner_{action}.cedar"),
        })
        checks.append({
            "name": f"floor_user_internal_{action}",
            "description": (
                f"user-role non-contractor MUST be permitted to {action} "
                "internal-classified Resources"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": f"Action::\"{action}\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, f"floor_user_internal_{action}.cedar"),
        })
        checks.append({
            "name": f"floor_contractor_mfa_confidential_{action}",
            "description": (
                f"user-role contractor with MFA verified MUST be permitted "
                f"to {action} confidential-classified Resources (§8.6 trap target)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": f"Action::\"{action}\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, f"floor_contractor_mfa_confidential_{action}.cedar"),
        })

    # ── Liveness (one per action) ─────────────────────────────
    for action in ("read", "write", "delete"):
        checks.append({
            "name": f"liveness_{action}",
            "description": f"User+{action}+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": f"Action::\"{action}\"",
            "resource_type": "Resource",
        })

    return checks
