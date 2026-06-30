permit (
    principal is User,
    action == Action::"AddToShareACL",
    resource is Document
)
when {
    principal in resource.manageACL &&
    context.is_authenticated &&
    context.requestTime <= resource.shareExpiry
};