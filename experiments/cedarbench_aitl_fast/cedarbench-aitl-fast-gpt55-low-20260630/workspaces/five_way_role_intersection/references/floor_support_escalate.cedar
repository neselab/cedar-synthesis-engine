// Floor: a user in the support role MUST be permitted to escalate any
// resource (the first link in the support → qa → developer → admin
// escalation chain).
permit (
    principal is User,
    action == Action::"escalate",
    resource is Resource
)
when {
    principal.role == "support" || principal.secondaryRoles.contains("support")
};
