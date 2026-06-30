// Ceiling for action adminOverride: permitted when role is any of the 25 declared roles.
permit (
    principal is User,
    action == Action::"adminOverride",
    resource is Order
)
when {
    principal.role == "viewer" || principal.role == "cs_agent" || principal.role == "cs_senior" || principal.role == "cs_manager" || principal.role == "cs_director" || principal.role == "fulfillment_basic" || principal.role == "fulfillment_lead" || principal.role == "fulfillment_manager" || principal.role == "warehouse" || principal.role == "returns_agent" || principal.role == "returns_lead" || principal.role == "finance_basic" || principal.role == "finance_senior" || principal.role == "finance_manager" || principal.role == "finance_director" || principal.role == "risk_analyst" || principal.role == "risk_manager" || principal.role == "pricing_analyst" || principal.role == "pricing_manager" || principal.role == "platform_ops" || principal.role == "platform_admin" || principal.role == "security_basic" || principal.role == "security_admin" || principal.role == "audit_read" || principal.role == "compliance_officer"
};
