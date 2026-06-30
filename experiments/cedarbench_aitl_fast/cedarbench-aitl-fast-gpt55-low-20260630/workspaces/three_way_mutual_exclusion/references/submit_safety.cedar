// Ceiling: submit permitted only when the principal is NOT the prior
// approver of this request AND NOT the prior auditor. Both checks are
// guarded against the optional context attribute being absent: when a
// prev attribute is missing, that pairing constraint is vacuously
// satisfied (no conflict can exist).
//
// §8.3 canonical positive form: every read of `context.prevX` is in a
// branch where `context has prevX` was already established, so the
// type-checker accepts it.
permit (
    principal is Engineer,
    action == Action::"submit",
    resource is ChangeRequest
)
when {
    (!(context has prevApprover) || (context has prevApprover && context.prevApprover != principal))
    && (!(context has prevAuditor) || (context has prevAuditor && context.prevAuditor != principal))
};
