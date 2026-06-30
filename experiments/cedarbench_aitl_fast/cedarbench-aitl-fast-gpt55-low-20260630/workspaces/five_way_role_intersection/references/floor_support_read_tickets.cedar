// Floor: a user in the support role MUST be permitted to read a
// resource of category "tickets".
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    (principal.role == "support" || principal.secondaryRoles.contains("support"))
    && resource.category == "tickets"
};
