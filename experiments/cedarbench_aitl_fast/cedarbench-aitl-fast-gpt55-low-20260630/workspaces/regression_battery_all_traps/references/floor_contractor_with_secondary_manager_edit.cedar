// Floor: a non-blocked user with primaryRole == "contractor" AND
// "manager" in secondaryRoles MUST be permitted to edit a document
// before its (graced) expiry — they're a manager via secondary role.
//
// §8.6 stress test (positive): catches the
//   forbid when primaryRole == "contractor"
// anti-pattern most directly. If the candidate writes that forbid,
// THIS floor witness lands on it and the floor fails.
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    !principal.isBlocked
    && context.now < resource.expiresAt.offset(context.graceWindow)
    && principal.primaryRole == "contractor"
    && principal.secondaryRoles.contains("manager")
};
