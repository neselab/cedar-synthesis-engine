// Floor: any Engineer MUST be permitted to audit a ChangeRequest when
// neither prevSubmitter nor prevApprover is attested in the context.
permit (
    principal is Engineer,
    action == Action::"audit",
    resource is ChangeRequest
)
when {
    !(context has prevSubmitter)
    && !(context has prevApprover)
};
