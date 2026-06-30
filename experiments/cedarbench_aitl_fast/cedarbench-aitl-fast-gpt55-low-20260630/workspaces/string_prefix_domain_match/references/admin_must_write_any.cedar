// Floor: a User whose email matches `admin@*` MUST be permitted to
// write ANY resource regardless of classification.
permit (
    principal is User,
    action == Action::"writeResource",
    resource is Resource
)
when {
    principal.email like "admin@*"
};
