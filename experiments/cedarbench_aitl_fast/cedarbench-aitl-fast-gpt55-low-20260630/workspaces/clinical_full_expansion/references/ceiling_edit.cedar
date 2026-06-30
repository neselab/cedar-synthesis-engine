permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    resource.projectStatus == "Active" &&
    context.hasPatientConsent == true &&
    (principal.department == resource.projectManagingDepartment || principal in Role::"GlobalAuditor") &&
    (
        (principal in Role::"ClinicalResearcher" && principal.clearanceLevel > 3 && resource.classification != "HighlyRestricted" && resource.studyPhase != "Phase-3") ||
        (principal in Role::"PrincipalInvestigator" && context.networkRiskScore < 20 && context.isCompliantDevice == true) ||
        (principal in Role::"DataManager" && principal.clearanceLevel > 5)
    ) &&
    (resource.classification != "HighlyRestricted" || context.isCompliantDevice == true)
};