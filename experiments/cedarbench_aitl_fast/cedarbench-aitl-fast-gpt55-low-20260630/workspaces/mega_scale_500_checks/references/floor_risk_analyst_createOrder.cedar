// Floor: user with role "risk_analyst" must be permitted to perform action createOrder.
permit (
    principal is User,
    action == Action::"createOrder",
    resource is Order
)
when {
    principal.role == "risk_analyst"
};
