// Floor: any non-blocked User MUST be permitted to read any Post,
// provided neither direction of the mutual-block relation holds.
permit (
    principal is User,
    action == Action::"readPost",
    resource is Post
)
when {
    !(principal in resource.author.blocked)
    && !(resource.author in principal.blocked)
};
