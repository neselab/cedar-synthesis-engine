// Floor: collecting personal/behavioral/geolocation data for a user
// under 13 MUST be permitted when verifiable parental consent has
// been obtained (parentalConsentToken present in context).
//
// The optional attribute requires a has-guard before any read; here
// we only need its presence, not its value, but the guard is still
// required for type-safety.
permit (
    principal is User,
    action == Action::"collect",
    resource is DataPoint
)
when {
    (resource.category == "personal"
     || resource.category == "behavioral"
     || resource.category == "geolocation")
    && context.now.durationSince(principal.dateOfBirth) < duration("4748d")
    && context has parentalConsentToken
};
