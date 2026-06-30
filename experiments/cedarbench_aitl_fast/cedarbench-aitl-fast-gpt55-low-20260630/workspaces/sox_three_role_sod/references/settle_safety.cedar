// Ceiling: settle_trade permitted only when ALL of:
//  - principal is a settlement_clerk or manager,
//  - principal is NOT the prior trade actor (cross-step SoD).
// The negated-has trap (§8.3) means the SoD check must be written as
// a fully-guarded disjunction: each side of `||` must have its own
// `has` guard before reading the optional attribute.
permit (
    principal is Employee,
    action == Action::"settle_trade",
    resource is Trade
)
when {
    (principal.role == "settlement_clerk" || principal.role == "manager")
    && (
        !(context has prevTradeActor)
        || (context has prevTradeActor && principal != context.prevTradeActor)
    )
};
