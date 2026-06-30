// Ceiling: ViewDocument — only owner or viewACL member (authenticated User)
permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
) when {
    context.is_authenticated &&
    (resource.owner == principal || principal in resource.viewACL)
};
