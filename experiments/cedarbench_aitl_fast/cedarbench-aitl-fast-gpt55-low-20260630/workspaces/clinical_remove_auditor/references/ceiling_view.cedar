permit (
    principal is User,
    action == Action::"View",
    resource is Document
) when {
    resource.projectStatus == "Active" &&
    principal.department == resource.projectManagingDepartment &&
    (
        (principal in Role::"ClinicalResearcher" && principal.clearanceLevel > 3 && resource.classification != "HighlyRestricted") ||
        (principal in Role::"PrincipalInvestigator" && context.networkRiskScore < 20 && context.isCompliantDevice == true)
    )
};