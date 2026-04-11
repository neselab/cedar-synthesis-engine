// Floor: the document's owner MUST be permitted to submit the document
// when it is in draft status.
permit (
    principal is User,
    action == Action::"submit",
    resource is Document
)
when {
    principal == resource.owner
    && resource.status == "draft"
};
