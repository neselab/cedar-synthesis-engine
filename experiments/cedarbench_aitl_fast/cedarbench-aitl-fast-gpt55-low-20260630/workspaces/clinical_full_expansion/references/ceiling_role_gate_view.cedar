permit (
    principal is User,
    action == Action::"View",
    resource is Document
)
when {
    principal in Role::"ClinicalResearcher" || principal in Role::"PrincipalInvestigator" || principal in Role::"DataManager"
};