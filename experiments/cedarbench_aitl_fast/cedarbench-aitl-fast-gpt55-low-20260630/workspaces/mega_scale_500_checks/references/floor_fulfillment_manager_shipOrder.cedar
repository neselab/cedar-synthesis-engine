// Floor: user with role "fulfillment_manager" must be permitted to perform action shipOrder.
permit (
    principal is User,
    action == Action::"shipOrder",
    resource is Order
)
when {
    principal.role == "fulfillment_manager"
};
