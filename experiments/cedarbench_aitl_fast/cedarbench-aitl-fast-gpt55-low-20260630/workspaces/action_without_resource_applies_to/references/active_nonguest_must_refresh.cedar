// Floor: any User with an active session AND a non-guest role MUST be
// permitted to refresh their token.
permit (
    principal is User,
    action == Action::"refreshToken",
    resource is Session
)
when {
    principal.sessionActive
    && principal.role != "guest"
};
