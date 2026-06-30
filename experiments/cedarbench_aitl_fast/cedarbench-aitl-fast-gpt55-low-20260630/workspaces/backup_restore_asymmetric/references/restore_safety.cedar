permit (principal is Operator, action == Action::"restore", resource is System)
when {
    (resource.environment == "staging" && (principal.role == "sre" || principal.role == "admin"))
    || (resource.environment == "production" && (principal.role == "admin" || (principal.role == "sre" && principal.isOnCall)))
};
