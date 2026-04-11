// Ceiling: viewOrder permitted only for the listed roles.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    (principal.role == "viewer" || principal.role == "cs_agent" || principal.role == "cs_manager" || principal.role == "fulfillment" || principal.role == "warehouse_lead" || principal.role == "returns" || principal.role == "finance_ops" || principal.role == "finance_manager" || principal.role == "platform_admin" || principal.role == "security_admin")
};
