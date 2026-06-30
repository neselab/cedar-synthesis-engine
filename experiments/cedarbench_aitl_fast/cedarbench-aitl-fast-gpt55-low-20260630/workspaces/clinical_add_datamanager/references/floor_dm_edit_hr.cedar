permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    principal in Role::"DataManager" &&
    principal.clearanceLevel > 5 &&
    resource.projectStatus == "Active" &&
    resource.classification == "HighlyRestricted" &&
    principal.department == resource.projectManagingDepartment
};