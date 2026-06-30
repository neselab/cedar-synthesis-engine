// Floor: user with role "fulfillment_basic" must be permitted to perform action viewOrder.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "fulfillment_basic"
};
