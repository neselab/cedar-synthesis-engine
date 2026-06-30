// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is Employee,
    action == Action::"useWorkstation",
    resource is Workstation
)
when {
    !resource.requiredTrainings.isEmpty() &&
    principal.completedTrainings.containsAll(resource.requiredTrainings)
};

permit (
    principal is Employee,
    action == Action::"bypass",
    resource is Workstation
)
when {
    principal.role == "admin"
};
