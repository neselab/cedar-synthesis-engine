permit (
    principal is Engineer,
    action == Action::"submit",
    resource is ChangeRequest
)
when {
    (!(context has prevApprover) || (context has prevApprover && context.prevApprover != principal)) &&
    (!(context has prevAuditor) || (context has prevAuditor && context.prevAuditor != principal))
};

permit (
    principal is Engineer,
    action == Action::"approve",
    resource is ChangeRequest
)
when {
    (!(context has prevSubmitter) || (context has prevSubmitter && context.prevSubmitter != principal)) &&
    (!(context has prevAuditor) || (context has prevAuditor && context.prevAuditor != principal))
};

permit (
    principal is Engineer,
    action == Action::"audit",
    resource is ChangeRequest
)
when {
    (!(context has prevSubmitter) || (context has prevSubmitter && context.prevSubmitter != principal)) &&
    (!(context has prevApprover) || (context has prevApprover && context.prevApprover != principal))
};