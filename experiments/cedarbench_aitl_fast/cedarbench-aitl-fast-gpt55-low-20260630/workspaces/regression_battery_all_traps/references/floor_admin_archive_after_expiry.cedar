// Floor: a non-blocked admin (primary or secondary) MUST be permitted
// to archive a document AFTER its expiry (no grace window for archive).
//
// §8.1 directional feedback: this floor LOOSENS admin archive in the
// post-expiry direction, while the read/edit floors TIGHTEN access in
// the pre-expiry direction. Diagnostics that don't separate
// implies-direction from floor-direction will misroute on this scenario.
//
// §8.8: !principal.isBlocked.
permit (
    principal is User,
    action == Action::"archive",
    resource is Document
)
when {
    !principal.isBlocked
    && context.now > resource.expiresAt
    && (principal.primaryRole == "admin" || principal.secondaryRoles.contains("admin"))
};
