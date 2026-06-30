// Ceiling: refreshToken permitted only when the principal has an active
// session AND is not a guest. Guest sessions do not get refreshed -- they
// expire on their stated lifetime and must re-login.
permit (
    principal is User,
    action == Action::"refreshToken",
    resource is Session
)
when {
    principal.sessionActive
    && principal.role != "guest"
};
