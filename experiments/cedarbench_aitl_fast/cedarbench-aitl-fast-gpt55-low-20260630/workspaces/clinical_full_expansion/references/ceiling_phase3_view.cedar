permit (
    principal is User,
    action == Action::"View",
    resource is Document
)
when {
    resource.studyPhase != "Phase-3" || principal in Role::"PrincipalInvestigator" || principal in Role::"DataManager"
};