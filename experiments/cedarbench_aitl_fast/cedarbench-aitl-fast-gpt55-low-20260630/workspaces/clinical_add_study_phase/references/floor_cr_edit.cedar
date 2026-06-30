permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
) when {
    principal in Role::"ClinicalResearcher" &&
    resource.projectStatus == "Active" &&
    principal.clearanceLevel > 3 &&
    resource.classification != "HighlyRestricted" &&
    resource.studyPhase != "Phase-3" &&
    principal.department == resource.projectManagingDepartment
};