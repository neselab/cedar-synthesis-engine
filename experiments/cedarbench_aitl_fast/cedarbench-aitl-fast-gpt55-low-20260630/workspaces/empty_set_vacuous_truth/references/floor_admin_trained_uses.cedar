// Floor: an admin who happens to have completed all trainings on a
// configured workstation MUST also be permitted to useWorkstation.
// (Admin role does not BLOCK use; it only adds bypass capability.)
permit (
    principal is Employee,
    action == Action::"useWorkstation",
    resource is Workstation
)
when {
    principal.role == "admin"
    && !resource.requiredTrainings.isEmpty()
    && principal.completedTrainings.containsAll(resource.requiredTrainings)
};
