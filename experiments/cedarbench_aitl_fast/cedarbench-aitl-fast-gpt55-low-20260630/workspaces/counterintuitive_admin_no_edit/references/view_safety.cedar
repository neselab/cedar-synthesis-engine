// Ceiling: view permitted only for editor, manager, or auditAdmin.
// (All three roles may view — auditAdmin's broad VIEW is intentional.)
permit (
    principal is Worker,
    action == Action::"view",
    resource is Record
)
when {
    principal.role == "editor"
    || principal.role == "manager"
    || principal.role == "auditAdmin"
};
