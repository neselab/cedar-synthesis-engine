// Floor: a user with clearance "restricted" in the matching department
// MUST be permitted to delete a dataset.
permit (
    principal is User,
    action == Action::"delete",
    resource is Dataset
)
when {
    principal.clearance == "restricted"
    && principal.department == resource.sourceDepartment
};
