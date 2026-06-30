// Ceiling: read is permitted only when the principal holds at least one
// role whose per-role read permit covers the resource's category.
//
// Role → allowed read categories:
//   admin     → any
//   auditor   → any
//   developer → "code", "logs"
//   qa        → "code", "tickets"
//   support   → "tickets"
//
// Role membership = (principal.role == R) OR (principal.secondaryRoles.contains(R)).
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    // admin — any category
    (principal.role == "admin" || principal.secondaryRoles.contains("admin"))
    // auditor — any category
    || (principal.role == "auditor" || principal.secondaryRoles.contains("auditor"))
    // developer — code or logs
    || (
        (principal.role == "developer" || principal.secondaryRoles.contains("developer"))
        && (resource.category == "code" || resource.category == "logs")
    )
    // qa — code or tickets
    || (
        (principal.role == "qa" || principal.secondaryRoles.contains("qa"))
        && (resource.category == "code" || resource.category == "tickets")
    )
    // support — tickets only
    || (
        (principal.role == "support" || principal.secondaryRoles.contains("support"))
        && resource.category == "tickets"
    )
};
