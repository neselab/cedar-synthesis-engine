permit (
    principal is User,
    action == Action::"View",
    resource is Document
)
when {
    principal in Role::"PrincipalInvestigator" &&
    principal in Role::"GlobalAuditor" &&
    resource.projectStatus == "Active" &&
    context.networkRiskScore < 20 &&
    context.isCompliantDevice == true &&
    resource.classification != "HighlyRestricted" &&
    resource.studyPhase != "Phase-3"
};