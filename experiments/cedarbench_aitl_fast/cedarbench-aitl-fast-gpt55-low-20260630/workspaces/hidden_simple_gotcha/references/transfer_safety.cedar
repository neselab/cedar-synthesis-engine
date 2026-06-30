// Ceiling: transfer may only be permitted when principal is the
// current owner. The creator does NOT retain transfer rights -- this
// is the inverse of the creator-read invariant.
permit (
    principal is User,
    action == Action::"transfer",
    resource is File
)
when {
    principal == resource.currentOwner
};
