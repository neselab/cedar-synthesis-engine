// Ceiling: delete permitted only when the user has the highest clearance
// ("restricted") AND their department matches the dataset's source department.
permit (
    principal is User,
    action == Action::"delete",
    resource is Dataset
)
when {
    principal.clearance == "restricted"
    && principal.department == resource.sourceDepartment
};
