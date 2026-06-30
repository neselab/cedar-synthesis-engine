// Floor: user with role "fulfillment_manager" must be permitted to perform action viewPII.
permit (
    principal is User,
    action == Action::"viewPII",
    resource is Order
)
when {
    principal.role == "fulfillment_manager"
};
