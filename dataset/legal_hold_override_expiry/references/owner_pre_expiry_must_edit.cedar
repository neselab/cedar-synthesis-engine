// Floor: the owner MUST be permitted to edit their document when the
// current time is before the expiry date.
permit (
    principal is User,
    action == Action::"editDocument",
    resource is Document
)
when {
    principal == resource.owner
    && context.now.datetime < resource.expiryDate
};
