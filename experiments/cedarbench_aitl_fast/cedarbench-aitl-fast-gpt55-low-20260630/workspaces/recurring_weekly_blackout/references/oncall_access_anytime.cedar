// Floor: an oncall user MUST be able to perform `access` at any time,
// inside or outside a blackout window.
permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "oncall"
};
