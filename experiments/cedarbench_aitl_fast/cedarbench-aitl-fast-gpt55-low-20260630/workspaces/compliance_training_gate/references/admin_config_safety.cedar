// Ceiling: adminConfig permitted only when employee is a manager
// AND has completed all required trainings.
permit (
    principal is Employee,
    action == Action::"adminConfig",
    resource is System
)
when {
    principal.role == "manager"
    && principal.completedTrainings.containsAll(resource.requiredTrainings)
};
