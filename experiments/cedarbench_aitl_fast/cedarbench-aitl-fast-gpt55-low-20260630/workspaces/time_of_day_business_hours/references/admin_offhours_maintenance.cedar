// Floor: an admin MUST be permitted to perform maintenance outside
// business hours.
permit (
    principal is User,
    action == Action::"maintenance",
    resource is System
)
when {
    principal.role == "admin"
    && (context.currentHour < 9 || context.currentHour >= 17)
};
