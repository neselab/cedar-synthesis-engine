// Floor: user with role "pricing_analyst" must be permitted to perform action bulkOperations.
permit (
    principal is User,
    action == Action::"bulkOperations",
    resource is Order
)
when {
    principal.role == "pricing_analyst"
};
