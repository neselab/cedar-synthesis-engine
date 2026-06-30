// Floor: an admin MUST be permitted to publish a draft document.
permit (
    principal is User,
    action == Action::"publish",
    resource is Document
)
when {
    principal.role == "admin" && resource.isDraft
};
