// Floor: an admin MUST be permitted to bypass a workstation.
permit (
    principal is Employee,
    action == Action::"bypass",
    resource is Workstation
)
when {
    principal.role == "admin"
};
