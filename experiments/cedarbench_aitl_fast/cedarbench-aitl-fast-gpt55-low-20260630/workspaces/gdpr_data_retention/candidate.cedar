permit (
    principal is User,
    action == Action::"read",
    resource is DataRecord
)
when {
    (principal.role == "processor" || principal.role == "controller" || principal.role == "dpo") &&
    resource.retentionExpiry > context.now &&
    resource.erasureRequested == false
};

permit (
    principal is User,
    action == Action::"process",
    resource is DataRecord
)
when {
    principal.role == "processor" &&
    resource.retentionExpiry > context.now &&
    resource.erasureRequested == false
};

permit (
    principal is User,
    action == Action::"delete",
    resource is DataRecord
)
when {
    principal.role == "controller" || principal.role == "dpo"
};

permit (
    principal is User,
    action == Action::"audit",
    resource is DataRecord
)
when {
    principal.role == "dpo"
};