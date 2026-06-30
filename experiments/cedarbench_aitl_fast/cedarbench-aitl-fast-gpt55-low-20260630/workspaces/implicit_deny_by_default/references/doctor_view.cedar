// Floor: a doctor MUST be permitted to view any patient chart.
permit (
    principal is Worker,
    action == Action::"view",
    resource is Chart
)
when {
    principal.role == "doctor"
};
