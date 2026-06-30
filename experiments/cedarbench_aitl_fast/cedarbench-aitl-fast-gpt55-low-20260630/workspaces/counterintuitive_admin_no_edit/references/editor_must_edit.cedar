// Floor: a Worker with role "editor" MUST be permitted to edit any
// Record. (Editors are the operational staff for record edits.)
permit (
    principal is Worker,
    action == Action::"edit",
    resource is Record
)
when {
    principal.role == "editor"
};
