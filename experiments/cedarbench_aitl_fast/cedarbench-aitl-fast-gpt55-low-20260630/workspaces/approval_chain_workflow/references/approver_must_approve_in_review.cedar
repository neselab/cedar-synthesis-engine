// Floor: any user in the document's requiredApprovers MUST be permitted
// to approve the document while it is in_review.
permit (
    principal is User,
    action == Action::"approve",
    resource is Document
)
when {
    principal in resource.requiredApprovers
    && resource.status == "in_review"
};
