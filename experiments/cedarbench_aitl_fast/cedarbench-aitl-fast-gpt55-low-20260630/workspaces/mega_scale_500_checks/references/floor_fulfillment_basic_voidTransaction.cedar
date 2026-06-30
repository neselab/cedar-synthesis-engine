// Floor: user with role "fulfillment_basic" must be permitted to perform action voidTransaction.
permit (
    principal is User,
    action == Action::"voidTransaction",
    resource is Order
)
when {
    principal.role == "fulfillment_basic"
};
