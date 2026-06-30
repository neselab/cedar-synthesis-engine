// Floor: user with role "pricing_analyst" must be permitted to perform action shipOrder.
permit (
    principal is User,
    action == Action::"shipOrder",
    resource is Order
)
when {
    principal.role == "pricing_analyst"
};
