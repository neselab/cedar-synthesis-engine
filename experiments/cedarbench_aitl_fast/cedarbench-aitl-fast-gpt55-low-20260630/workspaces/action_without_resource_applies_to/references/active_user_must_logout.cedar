// Floor: any User with an active session MUST be permitted to log out.
// (No global forbids in this scenario; the floor mirrors the ceiling.)
permit (
    principal is User,
    action == Action::"logout",
    resource is Session
)
when {
    principal.sessionActive
};
