// Floor: user with role "pricing_analyst" must be permitted to perform action partialRefund.
permit (
    principal is User,
    action == Action::"partialRefund",
    resource is Order
)
when {
    principal.role == "pricing_analyst"
};
