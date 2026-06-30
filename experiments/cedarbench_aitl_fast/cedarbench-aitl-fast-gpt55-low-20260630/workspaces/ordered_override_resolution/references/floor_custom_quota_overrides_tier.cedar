// Floor: when principal has customQuota and requestCount < customQuota,
// the call MUST be permitted -- regardless of tier.  This tests Rule 1
// (highest priority) winning over Rules 2 and 3.  In particular, an
// enterprise user with a small customQuota is bounded by the quota,
// not granted unlimited access; and a free user with a large
// customQuota is granted up to that quota, not capped at 10.
permit (
    principal is User,
    action == Action::"call",
    resource is Service
)
when {
    principal has customQuota
    && context.requestCount < principal.customQuota
};
