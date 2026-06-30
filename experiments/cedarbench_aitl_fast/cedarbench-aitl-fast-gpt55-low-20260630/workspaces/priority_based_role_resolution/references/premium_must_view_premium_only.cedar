// Floor: a User holding the "premium" role MUST be permitted to
// viewRecord on a Record whose tier is "premium-only".
permit (
    principal is User,
    action == Action::"viewRecord",
    resource is Record
)
when {
    principal.roles.contains("premium")
    && resource.tier == "premium-only"
};
