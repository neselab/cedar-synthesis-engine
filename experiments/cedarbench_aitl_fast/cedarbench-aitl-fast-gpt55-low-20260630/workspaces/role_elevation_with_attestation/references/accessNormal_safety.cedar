// Ceiling: accessNormal permitted only when baseRole is one of the
// three valid roles ("user", "lead", "manager"). No elevation or
// justification is required for normal access.
permit (
    principal is User,
    action == Action::"accessNormal",
    resource is SensitiveResource
)
when {
    principal.baseRole == "user"
    || principal.baseRole == "lead"
    || principal.baseRole == "manager"
};
