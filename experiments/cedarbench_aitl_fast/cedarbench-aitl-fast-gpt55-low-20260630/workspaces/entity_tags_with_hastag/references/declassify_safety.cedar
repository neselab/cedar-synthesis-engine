// Ceiling: declassify permitted only when the user holds a role tag whose
// value set contains "declassifier".
permit (
    principal is User,
    action == Action::"declassify",
    resource is Document
)
when {
    principal.hasTag("role")
    && principal.getTag("role").contains("declassifier")
};
