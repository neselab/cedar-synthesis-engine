permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
) when {
    principal in Role::"PrincipalInvestigator" &&
    resource.projectStatus == "Active" &&
    context.networkRiskScore < 20 &&
    context.isCompliantDevice == true &&
    principal.department == resource.projectManagingDepartment
};