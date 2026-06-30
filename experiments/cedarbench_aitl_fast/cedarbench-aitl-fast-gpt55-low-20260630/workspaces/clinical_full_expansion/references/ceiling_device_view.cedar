permit (
    principal is User,
    action == Action::"View",
    resource is Document
)
when {
    resource.classification != "HighlyRestricted" || context.isCompliantDevice == true
};