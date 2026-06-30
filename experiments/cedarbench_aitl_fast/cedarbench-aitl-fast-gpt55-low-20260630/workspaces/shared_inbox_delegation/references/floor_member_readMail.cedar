// Floor: a member MUST be able to readMail.
permit (
    principal is User,
    action == Action::"readMail",
    resource is Mailbox
)
when {
    resource.members.contains(principal)
};
