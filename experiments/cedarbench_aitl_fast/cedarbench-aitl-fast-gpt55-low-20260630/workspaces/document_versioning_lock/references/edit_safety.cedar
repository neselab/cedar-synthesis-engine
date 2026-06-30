// Ceiling: edit is permitted only for editor/admin AND the document is
// either unlocked or locked by this user.
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    (principal.role == "editor" || principal.role == "admin")
    && (!resource.isLocked || resource.lockedBy == principal)
};
