// Ceiling: readDocument permitted only when principal is the owner OR
// principal is a legal team member. Reading is unaffected by expiry or
// legal hold.
permit (
    principal is User,
    action == Action::"readDocument",
    resource is Document
)
when {
    principal == resource.owner || principal.isLegalTeam
};
