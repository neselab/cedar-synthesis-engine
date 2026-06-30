// Floor: user with role "pricing_analyst" must be permitted to perform action adminOverride.
permit (
    principal is User,
    action == Action::"adminOverride",
    resource is Order
)
when {
    principal.role == "pricing_analyst"
};
