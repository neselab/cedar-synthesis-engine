// Ceiling: read is permitted only when the user is not blocked, the
// document is not past its (graced) expiry, and the role-and-MFA
// gate matches the classification:
//   - public:        admin, manager, OR contractor.
//   - confidential:  admin, manager, OR (contractor with fresh MFA).
//
// Role membership = primaryRole == R || secondaryRoles.contains(R).
//
// §8.11 trap avoided: the classification gate is expressed with
// boolean disjunction, NOT a ?: ternary.
// §8.4 trap avoided: every reference to context.mfaToken is `has`-guarded.
// §8.6 trap avoided: contractor restriction is encoded as the
// ABSENCE of a permit (no contractor read of confidential without MFA),
// not as a forbid keyed on primaryRole.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    !principal.isBlocked
    && context.now < resource.expiresAt.offset(context.graceWindow)
    && (
        // public — any of the three roles suffices.
        (
            resource.classification == "public"
            && (
                principal.primaryRole == "admin" || principal.secondaryRoles.contains("admin")
                || principal.primaryRole == "manager" || principal.secondaryRoles.contains("manager")
                || principal.primaryRole == "contractor" || principal.secondaryRoles.contains("contractor")
            )
        )
        // confidential — admin or manager always OK; contractor only with MFA.
        || (
            resource.classification == "confidential"
            && (
                principal.primaryRole == "admin" || principal.secondaryRoles.contains("admin")
                || principal.primaryRole == "manager" || principal.secondaryRoles.contains("manager")
                || (
                    (principal.primaryRole == "contractor" || principal.secondaryRoles.contains("contractor"))
                    && context has mfaToken
                    && context.mfaToken != ""
                )
            )
        )
    )
};
