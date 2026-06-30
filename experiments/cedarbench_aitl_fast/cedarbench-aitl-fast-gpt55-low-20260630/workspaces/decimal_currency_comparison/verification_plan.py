"""Hand-authored verification plan for realworld/decimal_currency_comparison.

Tiered transaction approval using Cedar's `decimal` extension. The key
property under test is that the synthesizer uses METHOD-style comparison
on decimals (.lessThan, .lessThanOrEqual, .greaterThan, .greaterThanOrEqual)
rather than operator syntax (<, <=, >, >=), which Cedar rejects on
decimal values. There is also no arithmetic on decimals, so the
daily-limit check must compare accumulatedToday against dailyLimit
directly.

The common failure modes this scenario hunts:
  - Candidate writes `resource.amount < decimal("1000.0000")` (rejected
    by validator).
  - Candidate tries to compute `context.accumulatedToday + resource.amount`
    (no arithmetic on decimal).
  - Candidate permits a teller to approve above the tier cap.
  - Candidate permits a non-vp to reverse a transaction.
  - Candidate forgets the international cap or applies it to vp.

11 checks total (3 ceilings + 5 floors + 3 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "approve_safety",
            "description": (
                "approve permitted only when role tier matches amount, "
                "accumulatedToday < dailyLimit (teller/manager only), and "
                "international cap satisfied (teller/manager only); vp is "
                "exempt from all caps"
            ),
            "type": "implies",
            "principal_type": "Approver",
            "action": 'Action::"approve"',
            "resource_type": "Transaction",
            "reference_path": os.path.join(REFS, "approve_safety.cedar"),
        },
        {
            "name": "reverse_safety",
            "description": "reverse permitted only when the approver's role is vp",
            "type": "implies",
            "principal_type": "Approver",
            "action": 'Action::"reverse"',
            "resource_type": "Transaction",
            "reference_path": os.path.join(REFS, "reverse_safety.cedar"),
        },
        {
            "name": "audit_safety",
            "description": "audit permitted only when the principal is an Approver with a known role",
            "type": "implies",
            "principal_type": "Approver",
            "action": 'Action::"audit"',
            "resource_type": "Transaction",
            "reference_path": os.path.join(REFS, "audit_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "teller_small_domestic_approve",
            "description": (
                "A teller MUST be permitted to approve a domestic transaction "
                "under $1000.0000 when accumulatedToday is under the daily limit"
            ),
            "type": "floor",
            "principal_type": "Approver",
            "action": 'Action::"approve"',
            "resource_type": "Transaction",
            "floor_path": os.path.join(REFS, "teller_small_domestic_approve.cedar"),
        },
        {
            "name": "manager_mid_domestic_approve",
            "description": (
                "A manager MUST be permitted to approve a domestic transaction "
                "under $50000.0000 when accumulatedToday is under the daily limit"
            ),
            "type": "floor",
            "principal_type": "Approver",
            "action": 'Action::"approve"',
            "resource_type": "Transaction",
            "floor_path": os.path.join(REFS, "manager_mid_domestic_approve.cedar"),
        },
        {
            "name": "vp_any_approve",
            "description": "A VP MUST be permitted to approve any transaction at any amount",
            "type": "floor",
            "principal_type": "Approver",
            "action": 'Action::"approve"',
            "resource_type": "Transaction",
            "floor_path": os.path.join(REFS, "vp_any_approve.cedar"),
        },
        {
            "name": "vp_reverse",
            "description": "A VP MUST be permitted to reverse any transaction",
            "type": "floor",
            "principal_type": "Approver",
            "action": 'Action::"reverse"',
            "resource_type": "Transaction",
            "floor_path": os.path.join(REFS, "vp_reverse.cedar"),
        },
        {
            "name": "any_role_audit",
            "description": "Any approver (teller, manager, or vp) MUST be permitted to audit",
            "type": "floor",
            "principal_type": "Approver",
            "action": 'Action::"audit"',
            "resource_type": "Transaction",
            "floor_path": os.path.join(REFS, "any_role_audit.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_approve",
            "description": "Approver+approve+Transaction liveness",
            "type": "always-denies-liveness",
            "principal_type": "Approver",
            "action": 'Action::"approve"',
            "resource_type": "Transaction",
        },
        {
            "name": "liveness_reverse",
            "description": "Approver+reverse+Transaction liveness",
            "type": "always-denies-liveness",
            "principal_type": "Approver",
            "action": 'Action::"reverse"',
            "resource_type": "Transaction",
        },
        {
            "name": "liveness_audit",
            "description": "Approver+audit+Transaction liveness",
            "type": "always-denies-liveness",
            "principal_type": "Approver",
            "action": 'Action::"audit"',
            "resource_type": "Transaction",
        },
    ]
