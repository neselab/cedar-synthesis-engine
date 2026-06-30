// Floor: when both prevSubmitter and prevApprover are attested AND
// the auditing principal is neither of them, the audit MUST be
// permitted. This is the canonical "third independent reviewer" case
// the workflow exists to support.
permit (
    principal is Engineer,
    action == Action::"audit",
    resource is ChangeRequest
)
when {
    context has prevSubmitter
    && context has prevApprover
    && context.prevSubmitter != principal
    && context.prevApprover != principal
};
