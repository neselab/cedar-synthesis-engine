// Floor: a viewer MUST be permitted to updateCart an order with status=cart.
permit (
    principal is User,
    action == Action::"updateCart",
    resource is Order
)
when {
    principal.role == "viewer"
    && resource.status == "cart"
};
