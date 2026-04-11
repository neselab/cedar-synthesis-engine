// Ceiling: read is permitted only when the principal is the document's
// owner OR the principal is in the document's requiredApprovers. The
// read action is not gated on status — terminal-state documents remain
// readable by owners and approvers.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal == resource.owner
    || principal in resource.requiredApprovers
};
