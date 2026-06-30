// Floor: any user (even a non-owner) MUST be able to view a document
// that is not archived. Unarchived documents are world-readable.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    !resource.archived
};
