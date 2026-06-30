// Floor: a settlement_clerk who is NOT the prior trade actor MUST be
// permitted to settle_trade. The negated-has trap (§8.3) requires a
// fully-guarded disjunction so the floor stays jointly satisfiable.
permit (
    principal is Employee,
    action == Action::"settle_trade",
    resource is Trade
)
when {
    principal.role == "settlement_clerk"
    && (
        !(context has prevTradeActor)
        || (context has prevTradeActor && principal != context.prevTradeActor)
    )
};
