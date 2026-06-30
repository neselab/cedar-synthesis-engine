// Floor: any user in the document's requiredApprovers MUST be permitted
// to finalize when ALL required approvers have signed off AND the
// document is in_review. This tests the `.containsAll()` reasoning path.
permit (
    principal is User,
    action == Action::"finalize",
    resource is Document
)
when {
    principal in resource.requiredApprovers
    && resource.status == "in_review"
    && resource.currentApprovals.containsAll(resource.requiredApprovers)
};
