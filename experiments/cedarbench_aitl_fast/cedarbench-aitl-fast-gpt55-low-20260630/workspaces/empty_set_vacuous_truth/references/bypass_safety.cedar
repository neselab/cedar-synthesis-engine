// Ceiling: bypass permitted only when the principal has admin role.
permit (
    principal is Employee,
    action == Action::"bypass",
    resource is Workstation
)
when {
    principal.role == "admin"
};
