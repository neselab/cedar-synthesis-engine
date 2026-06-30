// Floor: a user whose role tag set contains "declassifier" MUST be
// permitted to declassify any Document.
permit (
    principal is User,
    action == Action::"declassify",
    resource is Document
)
when {
    principal.hasTag("role")
    && principal.getTag("role").contains("declassifier")
};
