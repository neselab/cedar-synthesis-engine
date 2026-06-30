// Ceiling: invoke is permitted ONLY when the per-type predicate holds.
// Candidate must be NO MORE permissive than this disjunction across the
// 6 principal types declared in `invoke.appliesTo`.
permit (principal, action == Action::"invoke", resource is Resource)
when {
    (principal is User && principal.mfaVerified) ||
    (principal is ApiKey && principal.scopes.contains("invoke")) ||
    (principal is ServiceAccount && principal.serviceName != "") ||
    (principal is Webhook && principal.signatureValid) ||
    (principal is BatchJob) ||
    (principal is Scheduler && principal.cronVerified)
};
