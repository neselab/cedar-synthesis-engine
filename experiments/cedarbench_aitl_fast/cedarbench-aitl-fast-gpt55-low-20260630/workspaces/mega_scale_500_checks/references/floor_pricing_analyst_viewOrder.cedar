// Floor: user with role "pricing_analyst" must be permitted to perform action viewOrder.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "pricing_analyst"
};
