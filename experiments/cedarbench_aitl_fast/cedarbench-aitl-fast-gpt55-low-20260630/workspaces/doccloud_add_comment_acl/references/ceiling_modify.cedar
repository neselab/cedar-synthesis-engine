// Ceiling: ModifyDocument — only owner or modifyACL member (authenticated)
permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
) when {
    context.is_authenticated &&
    (resource.owner == principal || principal in resource.modifyACL)
};
