// Floor: a user in the developer role MUST be permitted to read a
// resource of category "code".
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    (principal.role == "developer" || principal.secondaryRoles.contains("developer"))
    && resource.category == "code"
};
