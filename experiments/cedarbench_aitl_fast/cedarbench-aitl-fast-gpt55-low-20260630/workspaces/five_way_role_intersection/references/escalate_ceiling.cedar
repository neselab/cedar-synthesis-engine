// Ceiling: escalate is permitted only when the principal holds at least
// one of the three escalation-chain roles: support, qa, or developer.
// Admin is the top of the chain (cannot escalate further); auditor is
// off-chain.
permit (
    principal is User,
    action == Action::"escalate",
    resource is Resource
)
when {
    principal.role == "support" || principal.secondaryRoles.contains("support")
    || principal.role == "qa" || principal.secondaryRoles.contains("qa")
    || principal.role == "developer" || principal.secondaryRoles.contains("developer")
};
