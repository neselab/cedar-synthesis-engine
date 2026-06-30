// Ceiling: unlock is permitted only when the principal is the lock
// holder OR the principal is an admin.
permit (
    principal is User,
    action == Action::"unlock",
    resource is Document
)
when {
    principal == resource.lockedBy || principal.role == "admin"
};
