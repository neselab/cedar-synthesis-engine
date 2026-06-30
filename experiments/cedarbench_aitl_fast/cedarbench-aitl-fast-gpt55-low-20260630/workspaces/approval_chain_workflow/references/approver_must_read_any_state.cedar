// Floor: any required approver MUST be permitted to read the document
// in any state.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal in resource.requiredApprovers
};
