permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    resource.projectStatus == "Active" &&
    (
        (principal in Role::"ClinicalResearcher" && principal.clearanceLevel > 3 && resource.classification != "HighlyRestricted") ||
        (principal in Role::"PrincipalInvestigator" && context.networkRiskScore < 20 && context.isCompliantDevice == true)
    ) &&
    (
        principal.department == resource.projectManagingDepartment ||
        principal in Role::"GlobalAuditor"
    ) &&
    (resource.classification != "HighlyRestricted" || context.isCompliantDevice == true)
};