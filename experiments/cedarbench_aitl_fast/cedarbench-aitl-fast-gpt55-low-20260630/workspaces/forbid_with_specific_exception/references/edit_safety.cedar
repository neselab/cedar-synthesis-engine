// Ceiling: edit is permitted only when the user is the owner AND
// the document is NOT archived. Archived documents are immutable —
// no exception even for the owner.
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal == resource.owner && !resource.archived
};
