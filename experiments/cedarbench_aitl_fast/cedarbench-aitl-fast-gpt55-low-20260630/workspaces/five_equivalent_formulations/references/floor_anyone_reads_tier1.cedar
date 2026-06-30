// FLOOR: Any User MUST be permitted to read a tier-1 Doc.
// Tests the tier branch of the disjunction (covers non-admin users).
permit (
    principal,
    action == Action::"read",
    resource
)
when {
    resource.tier == 1
};
