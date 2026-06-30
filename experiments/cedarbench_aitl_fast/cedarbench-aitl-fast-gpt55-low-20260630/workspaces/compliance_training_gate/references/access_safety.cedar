// Ceiling: access permitted only when employee has completed all
// required trainings for the system.
permit (
    principal is Employee,
    action == Action::"access",
    resource is System
)
when {
    principal.completedTrainings.containsAll(resource.requiredTrainings)
};
