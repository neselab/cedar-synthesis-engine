// Floor B: a non-editor who owns the document MUST be permitted to edit it.
// This rules out a candidate that requires the editor role for all edits.
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal == resource.owner
    && principal.role != "editor"
};
