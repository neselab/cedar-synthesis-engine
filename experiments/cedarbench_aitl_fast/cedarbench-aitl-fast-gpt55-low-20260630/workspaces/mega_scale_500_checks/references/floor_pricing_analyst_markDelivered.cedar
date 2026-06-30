// Floor: user with role "pricing_analyst" must be permitted to perform action markDelivered.
permit (
    principal is User,
    action == Action::"markDelivered",
    resource is Order
)
when {
    principal.role == "pricing_analyst"
};
