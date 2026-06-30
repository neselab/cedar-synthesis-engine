// Ceiling: CommentOnDocument — only owner or commentACL member (authenticated)
permit (
    principal is User,
    action == Action::"CommentOnDocument",
    resource is Document
) when {
    context.is_authenticated &&
    (resource.owner == principal || principal in resource.commentACL)
};
