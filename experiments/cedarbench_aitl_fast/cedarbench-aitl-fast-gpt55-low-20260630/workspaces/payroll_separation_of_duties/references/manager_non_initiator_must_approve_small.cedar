// Floor: a manager who is NOT the initiator MUST be permitted to
// approve a small (< 50000) pending payroll entry.
permit (
    principal is User,
    action == Action::"approve",
    resource is PayrollEntry
)
when {
    principal.role == "manager"
    && resource.status == "pending_approval"
    && principal != resource.initiator
    && resource.amount < 50000
};
