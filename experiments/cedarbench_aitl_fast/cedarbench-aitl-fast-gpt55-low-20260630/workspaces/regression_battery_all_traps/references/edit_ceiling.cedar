// Ceiling: edit is permitted only when the user is not blocked, the
// document is not past its (graced) expiry, and the user holds the
// admin or manager role (primary or secondary). Contractors cannot
// edit, MFA notwithstanding.
//
// §8.6 trap avoided: contractor restriction is the ABSENCE of a
// contractor-permit, not a forbid on primaryRole.
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    !principal.isBlocked
    && context.now < resource.expiresAt.offset(context.graceWindow)
    && (
        principal.primaryRole == "admin" || principal.secondaryRoles.contains("admin")
        || principal.primaryRole == "manager" || principal.secondaryRoles.contains("manager")
    )
};
