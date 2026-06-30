// Floor: a delegate MUST be able to sendAs the mailbox.
permit (
    principal is User,
    action == Action::"sendAs",
    resource is Mailbox
)
when {
    resource.delegates.contains(principal)
};
