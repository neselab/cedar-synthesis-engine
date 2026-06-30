// Ceiling: under the most-restrictive reading of the hedged spec,
// `approve` is permitted ONLY when the principal has an explicit
// grant AND holds the "admin" role. "Only certain privileged users"
// is read as "admins only" — the strictest reading consistent with
// the spec. The candidate must be NO MORE permissive than this.
permit (
    principal is User,
    action == Action::"approve",
    resource is Document
)
when {
    principal.explicitGrant
    && principal.role == "admin"
};
