// Floor: a user with clearance "internal" or higher in the matching
// department MUST be permitted to derive from an internal dataset.
permit (
    principal is User,
    action == Action::"derive",
    resource is Dataset
)
when {
    (principal.clearance == "internal" || principal.clearance == "restricted")
    && resource.classification == "internal"
    && principal.department == resource.sourceDepartment
};
