permit (
    principal is User,
    action == Action::"viewByTag",
    resource is Document
)
when {
    !(resource.tags.isEmpty()) &&
    context.requestedTag != "" &&
    resource.tags.contains(context.requestedTag)
};