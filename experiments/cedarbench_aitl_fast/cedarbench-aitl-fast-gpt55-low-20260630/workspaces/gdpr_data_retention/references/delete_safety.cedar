// Ceiling: delete only when controller or dpo.
permit (
    principal is User,
    action == Action::"delete",
    resource is DataRecord
)
when {
    principal.role == "controller" || principal.role == "dpo"
};
