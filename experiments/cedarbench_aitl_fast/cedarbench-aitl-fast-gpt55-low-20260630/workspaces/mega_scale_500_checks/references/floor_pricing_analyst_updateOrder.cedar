// Floor: user with role "pricing_analyst" must be permitted to perform action updateOrder.
permit (
    principal is User,
    action == Action::"updateOrder",
    resource is Order
)
when {
    principal.role == "pricing_analyst"
};
