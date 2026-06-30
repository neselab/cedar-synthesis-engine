// Floor: user with role "fulfillment_manager" must be permitted to perform action markDelivered.
permit (
    principal is User,
    action == Action::"markDelivered",
    resource is Order
)
when {
    principal.role == "fulfillment_manager"
};
