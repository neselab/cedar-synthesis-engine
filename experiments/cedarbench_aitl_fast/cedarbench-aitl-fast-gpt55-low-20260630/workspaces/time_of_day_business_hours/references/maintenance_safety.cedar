// Ceiling: maintenance is permitted only when the user is an admin
// AND the request is outside business hours (currentHour < 9 OR
// currentHour >= 17).
permit (
    principal is User,
    action == Action::"maintenance",
    resource is System
)
when {
    principal.role == "admin"
    && (context.currentHour < 9 || context.currentHour >= 17)
};
