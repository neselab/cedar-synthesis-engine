// Floor: an employee who has completed all required trainings MUST
// be able to access the system.
permit (
    principal is Employee,
    action == Action::"access",
    resource is System
)
when {
    principal.completedTrainings.containsAll(resource.requiredTrainings)
};
