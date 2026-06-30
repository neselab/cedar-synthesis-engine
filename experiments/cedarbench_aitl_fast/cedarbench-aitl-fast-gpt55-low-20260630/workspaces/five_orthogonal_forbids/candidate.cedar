permit (
    principal is User,
    action == Action::"access",
    resource is Resource
);

forbid (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.isBlocked
};

forbid (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    resource.isArchived
};

forbid (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    resource.requiresMfa && !principal.mfaVerified
};

forbid (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    context.outsideBusinessHours
};

forbid (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    context.rateLimited
};