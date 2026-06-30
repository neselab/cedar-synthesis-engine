// Ceiling: reverse permitted only when the approver is a VP.
permit (
    principal is Approver,
    action == Action::"reverse",
    resource is Transaction
)
when {
    principal.role == "vp"
};
