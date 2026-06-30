// Floor: owner MUST be able to manage tags.
permit (
    principal is User,
    action == Action::"manageTags",
    resource is Document
)
when {
    principal == resource.owner
};
