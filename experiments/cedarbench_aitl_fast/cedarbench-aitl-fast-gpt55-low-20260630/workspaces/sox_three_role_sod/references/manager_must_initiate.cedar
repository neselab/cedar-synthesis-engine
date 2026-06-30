// Floor: a manager MUST be permitted to initiate_trade. Manager is
// a multi-step role explicitly allowed on initiation.
permit (
    principal is Employee,
    action == Action::"initiate_trade",
    resource is Trade
)
when {
    principal.role == "manager"
};
