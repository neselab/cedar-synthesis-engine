// Floor: a user (role == "user") at the specific level 0 must be permitted.
// Strict subset of user_low_level_must_permit but pins the rule on a
// specific value.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.role == "user"
    && resource.level == 0
};
