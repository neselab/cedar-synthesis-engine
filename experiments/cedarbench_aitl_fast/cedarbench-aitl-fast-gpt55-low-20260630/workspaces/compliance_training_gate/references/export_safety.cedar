// Ceiling: export permitted only when employee has completed all
// required trainings AND the system is not sensitive.
permit (
    principal is Employee,
    action == Action::"export",
    resource is System
)
when {
    principal.completedTrainings.containsAll(resource.requiredTrainings)
    && !resource.isSensitive
};
