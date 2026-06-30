// Floor: a manager who is NOT the prior trade actor MUST be permitted
// to settle_trade. Manager is allowed to settle so long as the
// cross-step SoD predicate is satisfied.
permit (
    principal is Employee,
    action == Action::"settle_trade",
    resource is Trade
)
when {
    principal.role == "manager"
    && (
        !(context has prevTradeActor)
        || (context has prevTradeActor && principal != context.prevTradeActor)
    )
};
