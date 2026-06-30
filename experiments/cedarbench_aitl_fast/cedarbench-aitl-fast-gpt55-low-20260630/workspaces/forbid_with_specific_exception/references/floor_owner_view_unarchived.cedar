// Floor: the owner MUST be able to view their own unarchived document.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal == resource.owner && !resource.archived
};
