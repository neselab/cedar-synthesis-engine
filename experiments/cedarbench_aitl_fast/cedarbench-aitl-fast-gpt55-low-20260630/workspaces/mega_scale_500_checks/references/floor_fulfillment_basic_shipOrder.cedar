// Floor: user with role "fulfillment_basic" must be permitted to perform action shipOrder.
permit (
    principal is User,
    action == Action::"shipOrder",
    resource is Order
)
when {
    principal.role == "fulfillment_basic"
};
