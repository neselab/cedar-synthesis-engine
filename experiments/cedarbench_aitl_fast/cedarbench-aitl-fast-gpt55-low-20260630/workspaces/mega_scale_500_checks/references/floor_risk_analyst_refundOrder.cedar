// Floor: user with role "risk_analyst" must be permitted to perform action refundOrder.
permit (
    principal is User,
    action == Action::"refundOrder",
    resource is Order
)
when {
    principal.role == "risk_analyst"
};
