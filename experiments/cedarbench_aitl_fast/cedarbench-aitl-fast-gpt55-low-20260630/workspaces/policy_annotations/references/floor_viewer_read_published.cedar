// Floor: viewer MUST read published articles.
permit (
    principal is User,
    action == Action::"read",
    resource is Article
)
when {
    principal.role == "viewer"
    && resource.isPublished
};
