// Floor: a user in the developer role MUST be permitted to escalate
// any resource (the third link in the support → qa → developer → admin
// escalation chain).
permit (
    principal is User,
    action == Action::"escalate",
    resource is Resource
)
when {
    principal.role == "developer" || principal.secondaryRoles.contains("developer")
};
