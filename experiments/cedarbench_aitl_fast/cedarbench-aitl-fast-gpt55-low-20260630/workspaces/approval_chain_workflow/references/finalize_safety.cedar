// Ceiling: finalize is permitted only when ALL of:
//   - principal is in the document's requiredApprovers,
//   - status is "in_review",
//   - all required approvers have signed off (currentApprovals ⊇ requiredApprovers).
//
// The `.containsAll()` check is the central safety property: a document
// cannot be finalized until every required approver has approved.
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
