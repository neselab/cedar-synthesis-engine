// Floor: a doctor MUST be permitted to edit any patient chart.
permit (
    principal is Worker,
    action == Action::"edit",
    resource is Chart
)
when {
    principal.role == "doctor"
};
