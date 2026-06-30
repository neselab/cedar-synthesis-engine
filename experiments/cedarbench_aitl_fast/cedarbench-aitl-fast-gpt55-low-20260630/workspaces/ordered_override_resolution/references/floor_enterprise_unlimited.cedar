// Floor: when the user has NO customQuota and tier == "enterprise",
// the call MUST be permitted regardless of requestCount.  This tests
// Rule 2 (medium priority) firing only when Rule 1 is inactive.
permit (
    principal is User,
    action == Action::"call",
    resource is Service
)
when {
    !(principal has customQuota)
    && principal.tier == "enterprise"
};
