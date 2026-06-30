// Ceiling: view is permitted only when the document is NOT archived,
// OR when the user is the owner of an archived document
// (read-only retention access).
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    !resource.archived || principal == resource.owner
};
