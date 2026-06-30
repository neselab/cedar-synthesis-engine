// Floor: a nurse MUST be permitted to view history of any prescription
// for care coordination.
permit (
    principal is User,
    action == Action::"viewHistory",
    resource is Prescription
)
when {
    principal.role == "nurse"
};
