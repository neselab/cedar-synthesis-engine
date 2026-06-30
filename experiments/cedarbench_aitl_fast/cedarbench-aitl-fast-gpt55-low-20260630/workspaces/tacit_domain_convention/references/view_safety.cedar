// Ceiling: view permitted only when role is viewer, editor, or admin.
// (Default deny: any other string -- empty or unknown -- must not get view.)
permit (
    principal is User,
    action == Action::"view",
    resource is Article
)
when {
    principal.role == "viewer"
    || principal.role == "editor"
    || principal.role == "admin"
};
