permit (
    principal is User,
    action == Action::"Export",
    resource is Document
)
when {
    resource.projectStatus == "Active" &&
    context.isCompliantDevice == true &&
    (
        (principal in Role::"ClinicalResearcher" &&
         principal.clearanceLevel > 3 &&
         resource.classification != "HighlyRestricted") ||
        (principal in Role::"PrincipalInvestigator" &&
         context.networkRiskScore < 20)
    )
};