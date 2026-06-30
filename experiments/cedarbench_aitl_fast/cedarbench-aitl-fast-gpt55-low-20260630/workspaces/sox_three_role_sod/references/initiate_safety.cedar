// Ceiling: initiate_trade permitted only when the principal is a
// trader or a manager. There is no SoD predicate on initiation
// because initiation is the first step of the workflow.
permit (
    principal is Employee,
    action == Action::"initiate_trade",
    resource is Trade
)
when {
    principal.role == "trader" || principal.role == "manager"
};
