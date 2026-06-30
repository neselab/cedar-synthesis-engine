permit (
    principal is User,
    action == Action::"View",
    resource is Document
)
when {
    principal.department == resource.projectManagingDepartment || principal in Role::"GlobalAuditor"
};