// Ceiling: access is permitted only when the user is a manager/admin
// (no time restriction) OR the request is during business hours
// (currentHour >= 9 AND currentHour < 17).
permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "manager"
    || principal.role == "admin"
    || (context.currentHour >= 9 && context.currentHour < 17)
};
