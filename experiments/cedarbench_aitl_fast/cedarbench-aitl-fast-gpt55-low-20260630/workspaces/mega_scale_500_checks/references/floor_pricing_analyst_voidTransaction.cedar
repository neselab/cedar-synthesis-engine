// Floor: user with role "pricing_analyst" must be permitted to perform action voidTransaction.
permit (
    principal is User,
    action == Action::"voidTransaction",
    resource is Order
)
when {
    principal.role == "pricing_analyst"
};
