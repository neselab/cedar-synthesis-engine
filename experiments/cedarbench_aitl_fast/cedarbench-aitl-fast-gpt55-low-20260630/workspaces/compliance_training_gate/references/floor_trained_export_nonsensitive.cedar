// Floor: an employee who has completed all required trainings MUST
// be able to export from a non-sensitive system.
// Per section 8.8: floor excludes the sensitive case because export is
// forbidden on sensitive systems.
permit (
    principal is Employee,
    action == Action::"export",
    resource is System
)
when {
    principal.completedTrainings.containsAll(resource.requiredTrainings)
    && !resource.isSensitive
};
