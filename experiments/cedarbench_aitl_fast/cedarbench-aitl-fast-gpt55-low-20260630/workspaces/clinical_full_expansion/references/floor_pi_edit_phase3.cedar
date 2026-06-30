permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    principal in Role::"PrincipalInvestigator" &&
    resource.projectStatus == "Active" &&
    resource.studyPhase == "Phase-3" &&
    context.networkRiskScore < 20 &&
    context.isCompliantDevice == true &&
    context.hasPatientConsent == true &&
    principal.department == resource.projectManagingDepartment &&
    resource.classification != "HighlyRestricted"
};