// Floor: user with role "returns_lead" must be permitted to perform action listOrders.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "returns_lead"
};
