// Floor: a User whose email matches `*@example.com` MUST be permitted
// to read an internal resource.
permit (
    principal is User,
    action == Action::"readResource",
    resource is Resource
)
when {
    principal.email like "*@example.com"
    && resource.classification == "internal"
};
