// Floor: a non-blocked manager (primary or secondary) MUST be
// permitted to edit a document before its (graced) expiry.
//
// This is the §8.6 stress test: a candidate that uses
//   forbid when { principal.primaryRole == "contractor" }
// to encode "contractors can't edit" will WRONGLY reject this
// floor's witness when the witness's primaryRole is "contractor"
// and "manager" is in secondaryRoles. The candidate must encode the
// restriction as the absence of a contractor permit, not a forbid.
//
// §8.8: !principal.isBlocked.
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    !principal.isBlocked
    && context.now < resource.expiresAt.offset(context.graceWindow)
    && (principal.primaryRole == "manager" || principal.secondaryRoles.contains("manager"))
};
