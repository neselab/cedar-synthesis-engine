// Ceiling: deleteRecord is permitted ONLY when the principal holds
// the admin role. Subscriber/premium/guest must never delete.
permit (
    principal is User,
    action == Action::"deleteRecord",
    resource is Record
)
when {
    principal.roles.contains("admin")
};
