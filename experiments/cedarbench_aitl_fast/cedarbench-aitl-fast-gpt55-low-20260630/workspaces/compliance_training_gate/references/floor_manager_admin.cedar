// Floor: a manager who has completed all required trainings MUST
// be able to adminConfig the system.
permit (
    principal is Employee,
    action == Action::"adminConfig",
    resource is System
)
when {
    principal.role == "manager"
    && principal.completedTrainings.containsAll(resource.requiredTrainings)
};
