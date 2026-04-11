// Ceiling: approve is permitted only when the principal is in the
// document's requiredApprovers AND the status is "in_review".
permit (
    principal is User,
    action == Action::"approve",
    resource is Document
)
when {
    principal in resource.requiredApprovers
    && resource.status == "in_review"
};
