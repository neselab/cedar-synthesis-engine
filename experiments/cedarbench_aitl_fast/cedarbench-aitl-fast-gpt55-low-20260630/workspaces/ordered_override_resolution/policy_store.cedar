// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"call",
    resource is Service
)
when {
    (principal has customQuota
        && context.requestCount < principal.customQuota)
    || (!(principal has customQuota)
        && principal.tier == "enterprise")
    || (!(principal has customQuota)
        && principal.tier == "free"
        && context.requestCount < 10)
    || (!(principal has customQuota)
        && principal.tier == "pro"
        && context.requestCount < 100)
};
