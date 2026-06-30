// Floor: a viewer MUST be permitted to viewOrder an order with status=refunded.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "viewer"
    && resource.status == "refunded"
};
