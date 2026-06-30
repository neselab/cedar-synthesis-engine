// Ceiling: read is permitted ONLY when principal is the document's owner.
// This single rule encodes all three restatements in the spec.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal == resource.owner
};
