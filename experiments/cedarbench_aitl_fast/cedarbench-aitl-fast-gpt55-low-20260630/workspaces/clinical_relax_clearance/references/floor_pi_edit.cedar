permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    principal in Role::"PrincipalInvestigator" &&
    context.networkRiskScore < 20 &&
    context.isCompliantDevice == true &&
    resource.projectStatus == "Active" &&
    principal.department == resource.projectManagingDepartment
};