// Floor: user with role "fulfillment_basic" must be permitted to perform action resolveDispute.
permit (
    principal is User,
    action == Action::"resolveDispute",
    resource is Order
)
when {
    principal.role == "fulfillment_basic"
};
