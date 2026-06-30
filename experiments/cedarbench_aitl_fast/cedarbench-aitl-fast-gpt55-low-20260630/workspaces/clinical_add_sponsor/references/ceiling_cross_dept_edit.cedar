permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
) when {
    principal.department == resource.projectManagingDepartment ||
    principal in Role::"GlobalAuditor"
};