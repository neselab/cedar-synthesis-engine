permit (
    principal is User,
    action == Action::"Export",
    resource is Document
)
when {
    principal in Role::"ClinicalResearcher" &&
    principal.clearanceLevel > 3 &&
    resource.classification != "HighlyRestricted" &&
    resource.projectStatus == "Active" &&
    principal.department == resource.projectManagingDepartment &&
    context.isCompliantDevice == true
};