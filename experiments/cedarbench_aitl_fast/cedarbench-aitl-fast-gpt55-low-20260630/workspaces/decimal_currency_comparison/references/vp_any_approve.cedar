// Floor: a VP MUST be permitted to approve any transaction,
// regardless of amount, daily limit, or international status.
permit (
    principal is Approver,
    action == Action::"approve",
    resource is Transaction
)
when {
    principal.role == "vp"
};
