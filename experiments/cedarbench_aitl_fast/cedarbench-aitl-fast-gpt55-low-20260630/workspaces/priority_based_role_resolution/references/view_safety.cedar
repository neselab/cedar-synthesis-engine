// Ceiling: viewRecord may be permitted only when the principal holds
// at least one role whose access tier covers the resource's tier.
//
// Tier-access table (encoded as a disjunction):
//   admin       => any tier
//   premium     => public, confidential, premium-only
//   subscriber  => public, confidential
//   guest       => public
//
// The candidate must NOT permit viewRecord under any combination
// outside this matrix.
permit (
    principal is User,
    action == Action::"viewRecord",
    resource is Record
)
when {
    (principal.roles.contains("admin"))
    || (principal.roles.contains("premium")
        && (resource.tier == "public"
            || resource.tier == "confidential"
            || resource.tier == "premium-only"))
    || (principal.roles.contains("subscriber")
        && (resource.tier == "public"
            || resource.tier == "confidential"))
    || (principal.roles.contains("guest")
        && resource.tier == "public")
};
