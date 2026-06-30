// Floor: a user in the qa role MUST be permitted to modify a resource
// of category "tickets".
permit (
    principal is User,
    action == Action::"modify",
    resource is Resource
)
when {
    (principal.role == "qa" || principal.secondaryRoles.contains("qa"))
    && resource.category == "tickets"
};
