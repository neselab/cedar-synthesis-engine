// Floor: any approver (teller, manager, or vp) MUST be permitted to
// audit any transaction.
permit (
    principal is Approver,
    action == Action::"audit",
    resource is Transaction
)
when {
    principal.role == "teller"
    || principal.role == "manager"
    || principal.role == "vp"
};
