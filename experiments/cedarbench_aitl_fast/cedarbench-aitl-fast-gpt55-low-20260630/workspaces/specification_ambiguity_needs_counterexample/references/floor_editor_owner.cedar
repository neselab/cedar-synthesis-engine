// Floor C: a user who is BOTH an editor AND the document owner MUST be
// permitted to edit. This is the trivial overlap case -- both permission
// paths apply simultaneously.
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal.role == "editor"
    && principal == resource.owner
};
