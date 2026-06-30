// Floor: a viewer MUST be permitted to view any article.
// No global forbids in this scenario, so no exclusions needed (S8.8).
permit (
    principal is User,
    action == Action::"view",
    resource is Article
)
when {
    principal.role == "viewer"
};
