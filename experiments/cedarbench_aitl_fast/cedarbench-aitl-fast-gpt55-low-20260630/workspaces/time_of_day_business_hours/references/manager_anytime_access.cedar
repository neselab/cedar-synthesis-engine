// Floor: a manager MUST be permitted to access the system at any hour.
permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "manager"
};
