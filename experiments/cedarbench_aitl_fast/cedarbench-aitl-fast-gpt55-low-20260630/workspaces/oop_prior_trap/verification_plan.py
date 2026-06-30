"""Hand-authored verification plan for realworld/oop_prior_trap.

Adversarial scenario: entity names (AccountManager, BankAccount)
are deliberately Java/C#-flavored to maximize the pull of an
object-oriented prior on the Phase-2 synthesizer. Common OOP idioms
that are INVALID Cedar:

  - principal.getAccountList()   — no methods on user-defined entities
  - resource.isOpen()            — no methods on user-defined entities
  - resource.balance != null     — no null in Cedar
  - principal instanceof AccountManager — must be `is`
  - principal.accountList.contains(resource.accountHolder)
                                 — type error: Set<String> vs User
  - chained method navigation, getter syntax, etc.

The intended converged candidate is three small `permit` policies
(one per action) using attribute reads and operator equality.

Plan totals: 3 ceilings + 4 floors + 3 liveness = 10 checks.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    checks = []

    # ── Safety ceilings ──────────────────────────────────────
    checks.append({
        "name": "viewBalance_safety",
        "description": (
            "viewBalance permitted only when manager's accountList "
            "contains the holder's userId AND account is not CLOSED"
        ),
        "type": "implies",
        "principal_type": "AccountManager",
        "action": "Action::\"viewBalance\"",
        "resource_type": "BankAccount",
        "reference_path": os.path.join(REFS, "viewBalance_safety.cedar"),
    })
    checks.append({
        "name": "transferFunds_safety",
        "description": (
            "transferFunds permitted only when manager's accountList "
            "contains the holder's userId AND status == OPEN AND "
            "balance > 0"
        ),
        "type": "implies",
        "principal_type": "AccountManager",
        "action": "Action::\"transferFunds\"",
        "resource_type": "BankAccount",
        "reference_path": os.path.join(REFS, "transferFunds_safety.cedar"),
    })
    checks.append({
        "name": "closeAccount_safety",
        "description": (
            "closeAccount permitted only when principal.roleType == "
            "\"manager\" AND resource.balance == 0 (no accountList "
            "requirement)"
        ),
        "type": "implies",
        "principal_type": "AccountManager",
        "action": "Action::\"closeAccount\"",
        "resource_type": "BankAccount",
        "reference_path": os.path.join(REFS, "closeAccount_safety.cedar"),
    })

    # ── Floors ───────────────────────────────────────────────
    checks.append({
        "name": "floor_view_listed_open",
        "description": (
            "Listed-customer + OPEN-status accounts MUST be viewable"
        ),
        "type": "floor",
        "principal_type": "AccountManager",
        "action": "Action::\"viewBalance\"",
        "resource_type": "BankAccount",
        "floor_path": os.path.join(REFS, "floor_view_listed_open.cedar"),
    })
    checks.append({
        "name": "floor_view_listed_frozen",
        "description": (
            "Listed-customer + FROZEN-status accounts MUST be viewable "
            "(frozen accounts are inspectable for balance)"
        ),
        "type": "floor",
        "principal_type": "AccountManager",
        "action": "Action::\"viewBalance\"",
        "resource_type": "BankAccount",
        "floor_path": os.path.join(REFS, "floor_view_listed_frozen.cedar"),
    })
    checks.append({
        "name": "floor_transfer_listed_open_positive",
        "description": (
            "Happy-path transfer (listed + OPEN + positive balance) "
            "MUST be permitted"
        ),
        "type": "floor",
        "principal_type": "AccountManager",
        "action": "Action::\"transferFunds\"",
        "resource_type": "BankAccount",
        "floor_path": os.path.join(REFS, "floor_transfer_listed_open_positive.cedar"),
    })
    checks.append({
        "name": "floor_close_manager_zero",
        "description": (
            "Manager closing a zero-balance account MUST be permitted"
        ),
        "type": "floor",
        "principal_type": "AccountManager",
        "action": "Action::\"closeAccount\"",
        "resource_type": "BankAccount",
        "floor_path": os.path.join(REFS, "floor_close_manager_zero.cedar"),
    })

    # ── Liveness ─────────────────────────────────────────────
    checks.append({
        "name": "liveness_viewBalance",
        "description": "AccountManager+viewBalance+BankAccount liveness",
        "type": "always-denies-liveness",
        "principal_type": "AccountManager",
        "action": "Action::\"viewBalance\"",
        "resource_type": "BankAccount",
    })
    checks.append({
        "name": "liveness_transferFunds",
        "description": "AccountManager+transferFunds+BankAccount liveness",
        "type": "always-denies-liveness",
        "principal_type": "AccountManager",
        "action": "Action::\"transferFunds\"",
        "resource_type": "BankAccount",
    })
    checks.append({
        "name": "liveness_closeAccount",
        "description": "AccountManager+closeAccount+BankAccount liveness",
        "type": "always-denies-liveness",
        "principal_type": "AccountManager",
        "action": "Action::\"closeAccount\"",
        "resource_type": "BankAccount",
    })

    return checks
