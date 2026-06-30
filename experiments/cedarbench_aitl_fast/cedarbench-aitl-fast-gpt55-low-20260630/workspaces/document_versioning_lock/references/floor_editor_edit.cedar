// Floor: an editor MUST be permitted to edit an unlocked document.
// §8.8: The floor includes !resource.isLocked to be jointly satisfiable
// with the edit ceiling's lock-bypass condition.
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal.role == "editor" && !resource.isLocked
};
