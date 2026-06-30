// Ceiling: read is permitted only when one of the three rules applies.
// - docs/*  (any user)
// - reports/<any>*-final, where * is a LITERAL asterisk (role == "user" only)
// - system/* (role == "admin" only)
permit (
    principal is User,
    action == Action::"read",
    resource is File
)
when {
    resource.path like "docs/*"
    || (principal.role == "user" && resource.path like "reports/*\*-final")
    || (principal.role == "admin" && resource.path like "system/*")
};
