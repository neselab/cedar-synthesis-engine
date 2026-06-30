// Floor: a non-blocked manager (primary or secondary) MUST be
// permitted to read a confidential document before expiry, EVEN
// when no MFA token is supplied (mfaToken absent from context).
//
// §8.11 stress test: a candidate that flattens the classification
// gate into `contractor ? mfa_required : false` ternary will likely
// also accidentally require MFA for managers. This floor with an
// absent mfaToken catches that mistake.
//
// §8.4 demonstration: this floor does NOT touch context.mfaToken
// at all — the policy must permit managers without ever reading
// that optional attribute.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    !principal.isBlocked
    && resource.classification == "confidential"
    && context.now < resource.expiresAt.offset(context.graceWindow)
    && (principal.primaryRole == "manager" || principal.secondaryRoles.contains("manager"))
};
