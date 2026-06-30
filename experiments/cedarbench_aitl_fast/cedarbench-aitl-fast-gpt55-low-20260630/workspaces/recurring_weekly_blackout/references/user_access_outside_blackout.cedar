// Floor: an ordinary user MUST be able to perform `access` when the
// host attests we are NOT in a blackout window.
permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "user"
    && context.inBlackoutWindow == false
};
