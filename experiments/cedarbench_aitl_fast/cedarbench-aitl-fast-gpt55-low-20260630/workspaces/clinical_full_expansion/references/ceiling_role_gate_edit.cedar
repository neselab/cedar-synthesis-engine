permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    principal in Role::"ClinicalResearcher" || principal in Role::"PrincipalInvestigator" || principal in Role::"DataManager"
};