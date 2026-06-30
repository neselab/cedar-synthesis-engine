// Ceiling: modify is permitted only when the principal holds at least
// one role whose per-role modify permit covers the resource's category.
//
// Role → allowed modify categories:
//   admin     → any
//   developer → "code", "config"
//   qa        → "tickets"
//   auditor, support → none
permit (
    principal is User,
    action == Action::"modify",
    resource is Resource
)
when {
    (principal.role == "admin" || principal.secondaryRoles.contains("admin"))
    || (
        (principal.role == "developer" || principal.secondaryRoles.contains("developer"))
        && (resource.category == "code" || resource.category == "config")
    )
    || (
        (principal.role == "qa" || principal.secondaryRoles.contains("qa"))
        && resource.category == "tickets"
    )
};
