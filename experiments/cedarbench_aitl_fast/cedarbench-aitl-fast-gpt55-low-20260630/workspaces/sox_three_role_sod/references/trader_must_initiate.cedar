// Floor: a trader MUST be permitted to initiate_trade. There are no
// global forbids in this spec to consistency-check against (§8.8).
permit (
    principal is Employee,
    action == Action::"initiate_trade",
    resource is Trade
)
when {
    principal.role == "trader"
};
