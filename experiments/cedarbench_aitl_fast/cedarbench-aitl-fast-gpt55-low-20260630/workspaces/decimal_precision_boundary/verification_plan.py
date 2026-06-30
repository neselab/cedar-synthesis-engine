"""Hand-authored verification plan for realworld/decimal_precision_boundary.

High-precision financial gates exercising Cedar's `decimal` extension at
the edges of its representable range and the constraints of its
method-only comparison API.

Cedar `decimal`:
  - Range: -922337203685477.5808 .. 922337203685477.5807 (signed
    64-bit fixed point, 4-digit fractional part).
  - Constructed only from string literals: `decimal("0.0001")`,
    `decimal("1000000.0000")`. The string MUST contain a `.` and have
    1 to 4 fractional digits; `decimal("100")` is rejected at parse
    time.
  - NO arithmetic: `+`, `-`, `*`, `/` are not defined for decimal.
  - NO standard comparison operators: `<`, `>`, `<=`, `>=` are not
    overloaded for decimal. The only comparisons are the four methods
    `.lessThan`, `.lessThanOrEqual`, `.greaterThan`,
    `.greaterThanOrEqual`.

Common LLM failure modes hunted by this plan:
  - Candidate writes `resource.balance > 0` or
    `resource.amount <= 1000000` -- rejected by `cedar validate`
    because comparison operators are not defined on decimal.
  - Candidate constructs decimals from numeric literals
    (`decimal(0.0001)`) or fewer/more than 1-4 fractional digits
    (`decimal("0")`, `decimal("0.00001")`) -- both are runtime errors.
  - Candidate uses `.lessThan` where it should be `.lessThanOrEqual`,
    accidentally excluding the inclusive upper-bound case
    (caught by floor_transfer_at_upper_bound).
  - Candidate flips the threshold and writes
    `decimal("0.0001").greaterThan(resource.balance)` (the threshold
    on the receiver side), inverting the gate.
  - Candidate forgets the lower bound on `transfer` and lets a
    zero-amount or negative-amount transaction through (caught by
    transfer_safety with the `greaterThan(decimal("0.0000"))` clause).
  - Candidate adds gating to `viewBalance` (e.g. requires the user to
    own the account) and so fails floor_viewBalance_any.

10 checks total (3 ceilings + 4 floors + 3 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "withdraw_safety",
            "description": "withdraw permitted only when account balance is strictly positive (balance.greaterThan(decimal('0.0001')))",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"withdraw"',
            "resource_type": "Account",
            "reference_path": os.path.join(REFS, "withdraw_safety.cedar"),
        },
        {
            "name": "transfer_safety",
            "description": "transfer permitted only when amount is strictly positive AND <= 1,000,000.0000, both via decimal method comparisons",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"transfer"',
            "resource_type": "Transaction",
            "reference_path": os.path.join(REFS, "transfer_safety.cedar"),
        },
        {
            "name": "viewBalance_safety",
            "description": "viewBalance has no decimal-driven restriction; ceiling is unconditional permit",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"viewBalance"',
            "resource_type": "Account",
            "reference_path": os.path.join(REFS, "viewBalance_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_withdraw_positive",
            "description": "Account with balance strictly greater than decimal('0.0001') MUST be withdrawable",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"withdraw"',
            "resource_type": "Account",
            "floor_path": os.path.join(REFS, "floor_withdraw_positive.cedar"),
        },
        {
            "name": "floor_transfer_in_range",
            "description": "Transaction with amount strictly positive AND <= 1,000,000.0000 MUST be permitted",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"transfer"',
            "resource_type": "Transaction",
            "floor_path": os.path.join(REFS, "floor_transfer_in_range.cedar"),
        },
        {
            "name": "floor_transfer_at_upper_bound",
            "description": "Transaction with amount equal to exactly decimal('1000000.0000') MUST be permitted (boundary inclusive)",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"transfer"',
            "resource_type": "Transaction",
            "floor_path": os.path.join(REFS, "floor_transfer_at_upper_bound.cedar"),
        },
        {
            "name": "floor_viewBalance_any",
            "description": "Any User MUST be permitted to viewBalance on any Account",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"viewBalance"',
            "resource_type": "Account",
            "floor_path": os.path.join(REFS, "floor_viewBalance_any.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_withdraw",
            "description": "User+withdraw+Account liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"withdraw"',
            "resource_type": "Account",
        },
        {
            "name": "liveness_transfer",
            "description": "User+transfer+Transaction liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"transfer"',
            "resource_type": "Transaction",
        },
        {
            "name": "liveness_viewBalance",
            "description": "User+viewBalance+Account liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"viewBalance"',
            "resource_type": "Account",
        },
    ]
