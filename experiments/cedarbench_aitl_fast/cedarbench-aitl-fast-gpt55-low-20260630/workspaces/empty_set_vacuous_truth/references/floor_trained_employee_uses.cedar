// Floor: an employee whose completed trainings cover all required trainings
// of a CONFIGURED (non-empty) workstation MUST be permitted to use it.
permit (
    principal is Employee,
    action == Action::"useWorkstation",
    resource is Workstation
)
when {
    !resource.requiredTrainings.isEmpty()
    && principal.completedTrainings.containsAll(resource.requiredTrainings)
};
