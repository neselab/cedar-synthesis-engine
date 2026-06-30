// Ceiling: audit_trade permitted only when ALL of:
//  - principal is an auditor (hard role gate, no manager fallback),
//  - principal is NOT the prior trade actor,
//  - principal is NOT the prior settle actor.
// Both optional attributes need fully-guarded disjunctions to avoid
// the negated-has trap (§8.3).
permit (
    principal is Employee,
    action == Action::"audit_trade",
    resource is Trade
)
when {
    principal.role == "auditor"
    && (
        !(context has prevTradeActor)
        || (context has prevTradeActor && principal != context.prevTradeActor)
    )
    && (
        !(context has prevSettleActor)
        || (context has prevSettleActor && principal != context.prevSettleActor)
    )
};
