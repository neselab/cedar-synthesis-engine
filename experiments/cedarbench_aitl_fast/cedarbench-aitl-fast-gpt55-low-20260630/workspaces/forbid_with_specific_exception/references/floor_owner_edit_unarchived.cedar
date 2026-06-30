// Floor: the owner MUST be able to edit their own unarchived document.
// (No floor for archived edits — archived documents are immutable for
// all users, including the owner.)
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal == resource.owner && !resource.archived
};
