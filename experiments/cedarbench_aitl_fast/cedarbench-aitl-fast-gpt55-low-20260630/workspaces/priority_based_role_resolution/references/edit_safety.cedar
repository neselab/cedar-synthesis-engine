// Ceiling: editRecord is permitted ONLY when the principal holds the
// admin role. Subscriber/premium/guest must never edit.
permit (
    principal is User,
    action == Action::"editRecord",
    resource is Record
)
when {
    principal.roles.contains("admin")
};
