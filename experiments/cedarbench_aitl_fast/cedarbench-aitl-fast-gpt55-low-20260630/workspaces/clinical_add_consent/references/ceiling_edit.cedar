permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    resource.projectStatus == "Active" &&
    context.hasPatientConsent == true &&
    (
        (principal in Role::"ClinicalResearcher" &&
         principal.clearanceLevel > 3 &&
         resource.classification != "HighlyRestricted") ||
        (principal in Role::"PrincipalInvestigator" &&
         context.networkRiskScore < 20 &&
         context.isCompliantDevice == true)
    )
};