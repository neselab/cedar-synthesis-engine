// Floor: the document owner MUST be permitted to read the document in
// any state, including terminal states (approved or rejected).
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal == resource.owner
};
