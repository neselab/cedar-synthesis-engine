// Floor: the owner MUST be permitted to delete their document when the
// current time is before expiry AND the document is not under legal hold.
permit (
    principal is User,
    action == Action::"deleteDocument",
    resource is Document
)
when {
    principal == resource.owner
    && context.now.datetime < resource.expiryDate
    && !resource.legalHold
};
