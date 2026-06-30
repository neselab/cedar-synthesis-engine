// Floor: a User holding the "subscriber" role MUST be permitted to
// viewRecord on a Record whose tier is "confidential".
permit (
    principal is User,
    action == Action::"viewRecord",
    resource is Record
)
when {
    principal.roles.contains("subscriber")
    && resource.tier == "confidential"
};
