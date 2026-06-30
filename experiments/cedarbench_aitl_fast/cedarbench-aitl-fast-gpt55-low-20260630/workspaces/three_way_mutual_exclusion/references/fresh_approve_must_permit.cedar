// Floor: any Engineer MUST be permitted to approve a ChangeRequest
// when neither prevSubmitter nor prevAuditor is attested in the
// context (the SoD constraints are vacuously satisfied).
permit (
    principal is Engineer,
    action == Action::"approve",
    resource is ChangeRequest
)
when {
    !(context has prevSubmitter)
    && !(context has prevAuditor)
};
