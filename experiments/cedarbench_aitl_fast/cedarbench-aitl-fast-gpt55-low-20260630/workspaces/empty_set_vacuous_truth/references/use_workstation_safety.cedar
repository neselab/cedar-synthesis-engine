// Ceiling: useWorkstation permitted only when requirements are non-empty
// AND the employee has completed every required training.
// The non-empty guard defeats the [].containsAll(...) == true vacuous-truth trap.
permit (
    principal is Employee,
    action == Action::"useWorkstation",
    resource is Workstation
)
when {
    !resource.requiredTrainings.isEmpty()
    && principal.completedTrainings.containsAll(resource.requiredTrainings)
};
