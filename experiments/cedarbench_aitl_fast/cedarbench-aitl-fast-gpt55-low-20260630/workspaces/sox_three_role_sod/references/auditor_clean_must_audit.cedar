// Floor: an auditor who is neither the prior trade actor nor the
// prior settle actor MUST be permitted to audit_trade. Both optional
// context attributes are has-guarded against the §8.3 trap.
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
