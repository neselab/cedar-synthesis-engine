// Floor: user with role "risk_analyst" must be permitted to perform action applyDiscount.
permit (
    principal is User,
    action == Action::"applyDiscount",
    resource is Order
)
when {
    principal.role == "risk_analyst"
};
