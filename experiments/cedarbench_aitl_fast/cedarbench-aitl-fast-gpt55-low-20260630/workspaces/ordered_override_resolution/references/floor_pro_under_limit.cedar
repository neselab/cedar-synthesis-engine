// Floor: when the user has NO customQuota, tier == "pro", and
// requestCount < 100, the call MUST be permitted.  This tests Rule 3
// (lowest priority) for the pro tier, firing only when Rules 1 and 2
// are inactive.
permit (
    principal is User,
    action == Action::"call",
    resource is Service
)
when {
    !(principal has customQuota)
    && principal.tier == "pro"
    && context.requestCount < 100
};
