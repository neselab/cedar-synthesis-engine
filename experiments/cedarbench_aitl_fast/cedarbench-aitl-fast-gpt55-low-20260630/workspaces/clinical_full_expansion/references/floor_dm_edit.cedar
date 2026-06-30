permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    principal in Role::"DataManager" &&
    resource.projectStatus == "Active" &&
    principal.clearanceLevel > 5 &&
    principal.department == resource.projectManagingDepartment &&
    context.hasPatientConsent == true &&
    context.isCompliantDevice == true &&
    resource.studyPhase != "Phase-3"
};