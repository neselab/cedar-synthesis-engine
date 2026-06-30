// Ceiling: submit is permitted only when the principal is the document's
// owner AND the document's status is "draft".
permit (
    principal is User,
    action == Action::"submit",
    resource is Document
)
when {
    principal == resource.owner
    && resource.status == "draft"
};
