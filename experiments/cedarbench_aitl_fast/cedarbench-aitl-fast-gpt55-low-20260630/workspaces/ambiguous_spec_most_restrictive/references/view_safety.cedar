// Ceiling: under the most-restrictive reading of the hedged spec,
// `view` is permitted ONLY when the principal has an explicit grant
// AND holds either the "admin" or "user" role. Any other role
// (e.g. "guest") is denied even with a grant. The candidate must
// be NO MORE permissive than this.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal.explicitGrant
    && (principal.role == "admin" || principal.role == "user")
};
