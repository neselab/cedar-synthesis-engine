// Floor: a VP MUST be permitted to reverse any transaction.
permit (
    principal is Approver,
    action == Action::"reverse",
    resource is Transaction
)
when {
    principal.role == "vp"
};
