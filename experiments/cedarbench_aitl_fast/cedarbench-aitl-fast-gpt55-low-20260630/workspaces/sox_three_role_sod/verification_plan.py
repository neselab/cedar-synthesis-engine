"""Hand-authored verification plan for realworld/sox_three_role_sod.

SOX-grade three-role separation of duties for banking. The trade
lifecycle splits into initiate -> settle -> audit, performed by
trader, settlement_clerk, and auditor respectively. The safety
property: no single principal may perform actions from any two of
those steps on the same trade.

Cross-step SoD is enforced via two host-supplied context attestations
(prevTradeActor and prevSettleActor) which are OPTIONAL. The negated-
has trap (§8.3) forces the SoD predicates to be written as fully
guarded disjunctions in both ceilings and floors.

Plan structure:
  - 3 ceilings: initiate / settle / audit safety bounds
  - 5 floors: trader+manager initiate, clerk+manager settle (both with
    SoD-clean attestations), auditor (clean of both prior steps)
  - 3 liveness: one per action
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "initiate_safety", "description": "initiate_trade permitted only when (trader OR manager)", "type": "implies", "principal_type": "Employee", "action": "Action::\"initiate_trade\"", "resource_type": "Trade", "reference_path": os.path.join(REFS, "initiate_safety.cedar")},
        {"name": "settle_safety", "description": "settle_trade permitted only when (clerk OR manager) AND principal != prevTradeActor", "type": "implies", "principal_type": "Employee", "action": "Action::\"settle_trade\"", "resource_type": "Trade", "reference_path": os.path.join(REFS, "settle_safety.cedar")},
        {"name": "audit_safety", "description": "audit_trade permitted only when auditor AND principal != prevTradeActor AND principal != prevSettleActor", "type": "implies", "principal_type": "Employee", "action": "Action::\"audit_trade\"", "resource_type": "Trade", "reference_path": os.path.join(REFS, "audit_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "trader_must_initiate", "description": "Trader MUST be permitted to initiate_trade", "type": "floor", "principal_type": "Employee", "action": "Action::\"initiate_trade\"", "resource_type": "Trade", "floor_path": os.path.join(REFS, "trader_must_initiate.cedar")},
        {"name": "manager_must_initiate", "description": "Manager MUST be permitted to initiate_trade", "type": "floor", "principal_type": "Employee", "action": "Action::\"initiate_trade\"", "resource_type": "Trade", "floor_path": os.path.join(REFS, "manager_must_initiate.cedar")},
        {"name": "clerk_non_initiator_must_settle", "description": "Settlement clerk who is NOT the prior trade actor MUST settle", "type": "floor", "principal_type": "Employee", "action": "Action::\"settle_trade\"", "resource_type": "Trade", "floor_path": os.path.join(REFS, "clerk_non_initiator_must_settle.cedar")},
        {"name": "manager_non_initiator_must_settle", "description": "Manager who is NOT the prior trade actor MUST settle", "type": "floor", "principal_type": "Employee", "action": "Action::\"settle_trade\"", "resource_type": "Trade", "floor_path": os.path.join(REFS, "manager_non_initiator_must_settle.cedar")},
        {"name": "auditor_clean_must_audit", "description": "Auditor who is neither prior trade nor prior settle actor MUST audit", "type": "floor", "principal_type": "Employee", "action": "Action::\"audit_trade\"", "resource_type": "Trade", "floor_path": os.path.join(REFS, "auditor_clean_must_audit.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_initiate_trade", "description": "Employee+initiate_trade+Trade liveness", "type": "always-denies-liveness", "principal_type": "Employee", "action": "Action::\"initiate_trade\"", "resource_type": "Trade"},
        {"name": "liveness_settle_trade", "description": "Employee+settle_trade+Trade liveness", "type": "always-denies-liveness", "principal_type": "Employee", "action": "Action::\"settle_trade\"", "resource_type": "Trade"},
        {"name": "liveness_audit_trade", "description": "Employee+audit_trade+Trade liveness", "type": "always-denies-liveness", "principal_type": "Employee", "action": "Action::\"audit_trade\"", "resource_type": "Trade"},
    ]
