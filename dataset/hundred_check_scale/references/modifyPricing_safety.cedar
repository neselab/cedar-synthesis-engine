// Ceiling: modifyPricing permitted only for the listed roles.
permit (
    principal is User,
    action == Action::"modifyPricing",
    resource is Order
)
when {
    (principal.role == "finance_manager" || principal.role == "platform_admin")
};
