// Floor: an administrator MUST be permitted to archive any patient chart.
permit (
    principal is Worker,
    action == Action::"archive",
    resource is Chart
)
when {
    principal.role == "administrator"
};
