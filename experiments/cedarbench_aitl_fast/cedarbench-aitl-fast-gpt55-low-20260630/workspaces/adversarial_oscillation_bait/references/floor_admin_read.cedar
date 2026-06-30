// FLOOR_ADMIN for `read`. Admins MUST be permitted regardless of
// resource classification or context.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal.role == "admin"
};
