// Floor: a legal team member MUST be permitted to read any document,
// regardless of expiry or legal hold status.
permit (
    principal is User,
    action == Action::"readDocument",
    resource is Document
)
when {
    principal.isLegalTeam
};
