// Floor: a cs_manager MUST be permitted to refundOrder an order with status=delivered.
permit (
    principal is User,
    action == Action::"refundOrder",
    resource is Order
)
when {
    principal.role == "cs_manager"
    && resource.status == "delivered"
};
