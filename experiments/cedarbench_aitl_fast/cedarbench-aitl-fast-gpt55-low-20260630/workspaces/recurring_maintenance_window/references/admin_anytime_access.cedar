// Floor: an admin MUST be able to perform the `access` action at any
// time, including during the maintenance window.
permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "admin"
};
