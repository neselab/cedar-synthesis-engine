// Floor: user with role "fulfillment_manager" must be permitted to perform action voidTransaction.
permit (
    principal is User,
    action == Action::"voidTransaction",
    resource is Order
)
when {
    principal.role == "fulfillment_manager"
};
