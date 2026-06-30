// Floor: any Engineer MUST be permitted to submit a fresh ChangeRequest
// (one that has not yet been approved or audited, so neither
// prevApprover nor prevAuditor is present in the context).
permit (
    principal is Engineer,
    action == Action::"submit",
    resource is ChangeRequest
)
when {
    !(context has prevApprover)
    && !(context has prevAuditor)
};
