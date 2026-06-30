permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
)
when {
    resource.projectStatus == "Active"
};