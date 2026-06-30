// Ceiling: approve permitted only when the principal is NOT the prior
// submitter of this request AND NOT the prior auditor. SoD requires
// that approval be done by an Engineer who has neither submitted nor
// audited this same change.
permit (
    principal is Engineer,
    action == Action::"approve",
    resource is ChangeRequest
)
when {
    (!(context has prevSubmitter) || (context has prevSubmitter && context.prevSubmitter != principal))
    && (!(context has prevAuditor) || (context has prevAuditor && context.prevAuditor != principal))
};
