// Floor: a cs_manager MUST be permitted to updateCart an order with status=cart.
permit (
    principal is User,
    action == Action::"updateCart",
    resource is Order
)
when {
    principal.role == "cs_manager"
    && resource.status == "cart"
};
