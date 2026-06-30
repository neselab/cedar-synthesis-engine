// Ceiling: readMail permitted only when principal is the owner,
// a delegate, or a member of the mailbox.
permit (
    principal is User,
    action == Action::"readMail",
    resource is Mailbox
)
when {
    principal == resource.owner
    || resource.delegates.contains(principal)
    || resource.members.contains(principal)
};
