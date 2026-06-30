// Floor: a user in the auditor role MUST be permitted to audit a
// resource of category "logs".
permit (
    principal is User,
    action == Action::"audit",
    resource is Resource
)
when {
    (principal.role == "auditor" || principal.secondaryRoles.contains("auditor"))
    && resource.category == "logs"
};
