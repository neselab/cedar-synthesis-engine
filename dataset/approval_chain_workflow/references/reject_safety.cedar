// Ceiling: reject is permitted only when the principal is in the
// document's requiredApprovers AND the status is "in_review". A single
// rejection blocks finalization (unanimous-consent workflow).
permit (
    principal is User,
    action == Action::"reject",
    resource is Document
)
when {
    principal in resource.requiredApprovers
    && resource.status == "in_review"
};
