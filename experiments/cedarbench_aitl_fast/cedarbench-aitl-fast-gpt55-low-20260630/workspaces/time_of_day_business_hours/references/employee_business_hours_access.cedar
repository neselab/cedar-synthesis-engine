// Floor: an employee MUST be permitted to access the system during
// business hours.
permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "employee"
    && context.currentHour >= 9
    && context.currentHour < 17
};
