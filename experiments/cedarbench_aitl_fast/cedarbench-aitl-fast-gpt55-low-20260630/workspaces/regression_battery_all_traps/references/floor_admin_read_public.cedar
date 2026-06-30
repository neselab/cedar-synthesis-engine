// Floor: a non-blocked admin (primary or secondary) MUST be permitted
// to read a public document before its (graced) expiry.
//
// §8.8: !principal.isBlocked is required because of the global
// "blocked users denied" forbid; without it the floor is unsatisfiable.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    !principal.isBlocked
    && resource.classification == "public"
    && context.now < resource.expiresAt.offset(context.graceWindow)
    && (principal.primaryRole == "admin" || principal.secondaryRoles.contains("admin"))
};
