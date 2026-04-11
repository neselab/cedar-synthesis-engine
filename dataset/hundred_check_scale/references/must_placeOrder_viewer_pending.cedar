// Floor: a viewer MUST be permitted to placeOrder an order with status=pending.
permit (
    principal is User,
    action == Action::"placeOrder",
    resource is Order
)
when {
    principal.role == "viewer"
    && resource.status == "pending"
};
