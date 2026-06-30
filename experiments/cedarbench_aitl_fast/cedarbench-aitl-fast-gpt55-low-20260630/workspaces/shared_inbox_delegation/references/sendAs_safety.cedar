// Ceiling: sendAs permitted only when principal is the owner
// or a delegate. Members cannot send as the mailbox.
permit (
    principal is User,
    action == Action::"sendAs",
    resource is Mailbox
)
when {
    principal == resource.owner
    || resource.delegates.contains(principal)
};
