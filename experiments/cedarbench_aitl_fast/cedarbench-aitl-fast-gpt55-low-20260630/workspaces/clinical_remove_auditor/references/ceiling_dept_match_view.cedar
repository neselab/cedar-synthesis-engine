permit (
    principal is User,
    action == Action::"View",
    resource is Document
) when {
    principal.department == resource.projectManagingDepartment
};