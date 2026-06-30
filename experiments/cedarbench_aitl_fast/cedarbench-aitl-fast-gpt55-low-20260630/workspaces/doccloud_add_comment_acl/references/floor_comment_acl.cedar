// Floor: A user in commentACL (who is NOT the owner) MUST be able to comment
// (Ensures commentACL membership is sufficient for commenting)
permit (
    principal is User,
    action == Action::"CommentOnDocument",
    resource is Document
) when {
    context.is_authenticated &&
    principal in resource.commentACL &&
    resource.owner != principal
};
