permit (
    principal is User,
    action == Action::"View",
    resource is Document
) when {
    resource.projectStatus == "Active" &&
    (
        (
            principal in Role::"ClinicalResearcher" &&
            principal.clearanceLevel > 3 &&
            resource.classification != "HighlyRestricted" &&
            resource.studyPhase != "Phase-3"
        ) ||
        (
            principal in Role::"PrincipalInvestigator" &&
            context.networkRiskScore < 20 &&
            context.isCompliantDevice == true
        )
    )
};