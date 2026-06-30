// Floor: the mailbox owner MUST be able to readMail.
permit (
    principal is User,
    action == Action::"readMail",
    resource is Mailbox
)
when {
    principal == resource.owner
};
