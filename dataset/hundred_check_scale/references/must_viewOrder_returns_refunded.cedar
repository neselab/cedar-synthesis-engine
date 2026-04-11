// Floor: a returns MUST be permitted to viewOrder an order with status=refunded.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "returns"
    && resource.status == "refunded"
};
