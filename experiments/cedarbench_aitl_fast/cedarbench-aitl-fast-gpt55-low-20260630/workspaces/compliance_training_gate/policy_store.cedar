// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is Employee,
    action == Action::"access",
    resource is System
)
when {
    principal.completedTrainings.containsAll(resource.requiredTrainings)
};

permit (
    principal is Employee,
    action == Action::"export",
    resource is System
)
when {
    principal.completedTrainings.containsAll(resource.requiredTrainings) &&
    !resource.isSensitive
};

permit (
    principal is Employee,
    action == Action::"adminConfig",
    resource is System
)
when {
    principal.role == "manager" &&
    principal.completedTrainings.containsAll(resource.requiredTrainings)
};
