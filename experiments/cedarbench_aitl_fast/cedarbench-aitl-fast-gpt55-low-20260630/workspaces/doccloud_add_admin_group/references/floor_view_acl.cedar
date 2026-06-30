permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    context.is_authenticated == true &&
    principal in resource.viewACL &&
    principal in resource.manageACL
};