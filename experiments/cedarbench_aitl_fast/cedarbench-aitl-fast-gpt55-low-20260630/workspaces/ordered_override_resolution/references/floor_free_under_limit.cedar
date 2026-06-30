// Floor: when the user has NO customQuota, tier == "free", and
// requestCount < 10, the call MUST be permitted.  This tests Rule 3
// (lowest priority) for the free tier, firing only when Rules 1 and 2
// are inactive.
permit (
    principal is User,
    action == Action::"call",
    resource is Service
)
when {
    !(principal has customQuota)
    && principal.tier == "free"
    && context.requestCount < 10
};
