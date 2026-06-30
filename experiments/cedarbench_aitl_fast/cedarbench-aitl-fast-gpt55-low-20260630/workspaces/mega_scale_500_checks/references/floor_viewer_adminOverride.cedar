// Floor: user with role "viewer" must be permitted to perform action adminOverride.
permit (
    principal is User,
    action == Action::"adminOverride",
    resource is Order
)
when {
    principal.role == "viewer"
};
