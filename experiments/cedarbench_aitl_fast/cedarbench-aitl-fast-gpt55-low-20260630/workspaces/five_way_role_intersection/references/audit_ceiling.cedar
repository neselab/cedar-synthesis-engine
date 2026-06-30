// Ceiling: audit is permitted only for auditor (any category) or
// developer on "logs".
permit (
    principal is User,
    action == Action::"audit",
    resource is Resource
)
when {
    (principal.role == "auditor" || principal.secondaryRoles.contains("auditor"))
    || (
        (principal.role == "developer" || principal.secondaryRoles.contains("developer"))
        && resource.category == "logs"
    )
};
