// Floor: user with role "fulfillment_lead" must be permitted to perform action markDelivered.
permit (
    principal is User,
    action == Action::"markDelivered",
    resource is Order
)
when {
    principal.role == "fulfillment_lead"
};
