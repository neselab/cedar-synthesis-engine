// Floor: any user in the document's requiredApprovers MUST be permitted
// to reject the document while it is in_review. A single rejection
// blocks finalization (unanimous consent workflow).
permit (
    principal is User,
    action == Action::"reject",
    resource is Document
)
when {
    principal in resource.requiredApprovers
    && resource.status == "in_review"
};
