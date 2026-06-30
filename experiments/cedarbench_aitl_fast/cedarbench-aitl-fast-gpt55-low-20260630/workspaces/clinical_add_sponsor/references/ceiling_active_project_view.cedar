permit (
    principal is User,
    action == Action::"View",
    resource is Document
) when {
    resource.projectStatus == "Active"
};