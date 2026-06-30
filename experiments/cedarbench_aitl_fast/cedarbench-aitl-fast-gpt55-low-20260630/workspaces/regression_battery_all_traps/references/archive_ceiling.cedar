// Ceiling: archive is permitted only when the user is not blocked,
// the document has expired (no grace), and the user holds the admin
// role (primary or secondary). This is intentionally the OPPOSITE
// time direction from read/edit — read/edit need now < expiry+grace;
// archive needs now > expiry. Drives §8.1 directional feedback.
permit (
    principal is User,
    action == Action::"archive",
    resource is Document
)
when {
    !principal.isBlocked
    && context.now > resource.expiresAt
    && (
        principal.primaryRole == "admin" || principal.secondaryRoles.contains("admin")
    )
};
