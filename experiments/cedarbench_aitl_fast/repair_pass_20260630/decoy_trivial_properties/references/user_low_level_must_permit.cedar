// Floor: a user (role == "user") with resource.level <= 3 must be permitted.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.role == "user"
    && resource.level <= 3
};
