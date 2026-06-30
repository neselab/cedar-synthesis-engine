// Floor: a non-blocked contractor (primary or secondary) WITH a
// fresh MFA token MUST be permitted to read a confidential document
// before expiry.
//
// §8.4: context.mfaToken is `has`-guarded.
// §8.6: contractor membership uses primary OR secondary role test —
//   a user with primaryRole == "contractor" AND secondaryRoles
//   .contains("manager") still satisfies this floor.
// §8.8: !principal.isBlocked excludes the global block-list.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    !principal.isBlocked
    && resource.classification == "confidential"
    && context.now < resource.expiresAt.offset(context.graceWindow)
    && (principal.primaryRole == "contractor" || principal.secondaryRoles.contains("contractor"))
    && context has mfaToken
    && context.mfaToken != ""
};
