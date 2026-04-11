// Ceiling: refundOrder permitted only for the listed roles and statuses.
permit (
    principal is User,
    action == Action::"refundOrder",
    resource is Order
)
when {
    (principal.role == "cs_manager" || principal.role == "finance_ops" || principal.role == "finance_manager")
    && (resource.status == "delivered")
};
