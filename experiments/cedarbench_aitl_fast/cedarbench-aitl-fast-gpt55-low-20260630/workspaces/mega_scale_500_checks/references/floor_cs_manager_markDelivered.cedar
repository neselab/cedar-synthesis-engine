// Floor: user with role "cs_manager" must be permitted to perform action markDelivered.
permit (
    principal is User,
    action == Action::"markDelivered",
    resource is Order
)
when {
    principal.role == "cs_manager"
};
