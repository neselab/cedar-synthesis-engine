// Floor: user with role "returns_agent" must be permitted to perform action refundOrder.
permit (
    principal is User,
    action == Action::"refundOrder",
    resource is Order
)
when {
    principal.role == "returns_agent"
};
