// Floor: user with role "risk_analyst" must be permitted to perform action voidTransaction.
permit (
    principal is User,
    action == Action::"voidTransaction",
    resource is Order
)
when {
    principal.role == "risk_analyst"
};
