// Ceiling: edit is permitted only when EITHER:
//   - principal.role == "editor" (regardless of ownership), OR
//   - principal == resource.owner (regardless of role).
// No other path grants edit.
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal.role == "editor"
    || principal == resource.owner
};
