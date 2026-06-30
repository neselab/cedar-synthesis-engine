// Ceiling: audit only when dpo.
permit (
    principal is User,
    action == Action::"audit",
    resource is DataRecord
)
when {
    principal.role == "dpo"
};
