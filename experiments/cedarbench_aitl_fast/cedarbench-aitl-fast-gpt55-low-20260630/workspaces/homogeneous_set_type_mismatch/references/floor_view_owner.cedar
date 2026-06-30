// Floor: the document's owner MUST be able to view it.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal == resource.owner
};
