// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is Employee,
    action == Action::"initiate_trade",
    resource is Trade
)
when {
    principal.role == "trader" || principal.role == "manager"
};

permit (
    principal is Employee,
    action == Action::"settle_trade",
    resource is Trade
)
when {
    (principal.role == "settlement_clerk" || principal.role == "manager") &&
    (
        !(context has prevTradeActor) ||
        ((context has prevTradeActor) && principal != context.prevTradeActor)
    )
};

permit (
    principal is Employee,
    action == Action::"audit_trade",
    resource is Trade
)
when {
    principal.role == "auditor" &&
    (
        !(context has prevTradeActor) ||
        ((context has prevTradeActor) && principal != context.prevTradeActor)
    ) &&
    (
        !(context has prevSettleActor) ||
        ((context has prevSettleActor) && principal != context.prevSettleActor)
    )
};
