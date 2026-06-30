// Floor: a User holding the "admin" role MUST be permitted to
// viewRecord on a Record whose tier is "admin-only".
permit (
    principal is User,
    action == Action::"viewRecord",
    resource is Record
)
when {
    principal.roles.contains("admin")
    && resource.tier == "admin-only"
};
