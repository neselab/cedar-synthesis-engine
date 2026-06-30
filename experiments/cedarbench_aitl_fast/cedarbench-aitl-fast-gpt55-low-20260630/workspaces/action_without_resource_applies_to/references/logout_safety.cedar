// Ceiling: logout permitted only when the principal currently has an active
// session. Logging out a user with no active session is a no-op at best and
// indicates a confused client at worst -- forbid it.
permit (
    principal is User,
    action == Action::"logout",
    resource is Session
)
when {
    principal.sessionActive
};
