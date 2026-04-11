// Ceiling: approve permitted only when ALL of:
//  - principal is a manager or cfo,
//  - entry is in pending_approval,
//  - principal is NOT the initiator (the SoD core check),
//  - AND if the amount is >= 50000, the principal is a cfo.
permit (
    principal is User,
    action == Action::"approve",
    resource is PayrollEntry
)
when {
    (principal.role == "manager" || principal.role == "cfo")
    && resource.status == "pending_approval"
    && principal != resource.initiator
    && (resource.amount < 50000 || principal.role == "cfo")
};
