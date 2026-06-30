// Floor: an oncall engineer MUST be able to access the system at any
// time, including during the maintenance window.
permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "oncall"
};
