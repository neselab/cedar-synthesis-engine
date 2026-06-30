// Floor: dpo MUST audit any record.
permit (
    principal is User,
    action == Action::"audit",
    resource is DataRecord
)
when {
    principal.role == "dpo"
};
