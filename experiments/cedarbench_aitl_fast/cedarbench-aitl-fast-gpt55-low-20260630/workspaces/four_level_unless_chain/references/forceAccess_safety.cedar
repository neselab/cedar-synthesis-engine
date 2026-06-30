// Ceiling: forceAccess permitted only for a commander holding the
// red-cell override token. All four context flags are irrelevant.
permit (
    principal is User,
    action == Action::"forceAccess",
    resource is Resource
)
when {
    principal.role == "commander" && principal.hasOverride
};
