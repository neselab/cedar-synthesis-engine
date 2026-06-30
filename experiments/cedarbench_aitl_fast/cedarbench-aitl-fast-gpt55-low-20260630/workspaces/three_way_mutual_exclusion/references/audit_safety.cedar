// Ceiling: audit permitted only when the principal is NOT the prior
// submitter of this request AND NOT the prior approver. The auditor
// must be independent of both upstream actors to provide a meaningful
// third-party review.
permit (
    principal is Engineer,
    action == Action::"audit",
    resource is ChangeRequest
)
when {
    (!(context has prevSubmitter) || (context has prevSubmitter && context.prevSubmitter != principal))
    && (!(context has prevApprover) || (context has prevApprover && context.prevApprover != principal))
};
