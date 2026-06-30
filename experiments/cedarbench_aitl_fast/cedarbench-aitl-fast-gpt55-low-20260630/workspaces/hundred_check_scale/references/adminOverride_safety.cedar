// Ceiling: adminOverride permitted only for the listed roles.
permit (
    principal is User,
    action == Action::"adminOverride",
    resource is Order
)
when {
    (principal.role == "platform_admin" || principal.role == "security_admin")
};
