permit (
    principal is User,
    action == Action::"Export",
    resource is Document
)
when {
    principal.department == resource.projectManagingDepartment ||
    principal in Role::"GlobalAuditor"
};