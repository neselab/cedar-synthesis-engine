permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    resource.studyPhase != "Phase-3" ||
    !(principal in Role::"ClinicalResearcher")
};