// Floor: user with role "fulfillment_lead" must be permitted to perform action cancelOrder.
permit (
    principal is User,
    action == Action::"cancelOrder",
    resource is Order
)
when {
    principal.role == "fulfillment_lead"
};
