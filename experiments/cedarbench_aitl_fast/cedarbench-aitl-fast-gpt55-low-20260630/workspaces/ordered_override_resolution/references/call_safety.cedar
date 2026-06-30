// Ceiling: call is permitted only when one of the three precedence-
// ordered branches matches.  Lower-priority branches are guarded with
// the negation of higher-priority conditions so the union of permits
// exactly reproduces the ordered semantics.
//
//   Rule 1 (highest): customQuota present -> requestCount < customQuota
//   Rule 2 (medium):  no customQuota AND tier == enterprise -> unlimited
//   Rule 3 (lowest):  no customQuota AND tier == free       -> < 10
//                     no customQuota AND tier == pro        -> < 100

permit (
    principal is User,
    action == Action::"call",
    resource is Service
)
when {
    // Rule 1 -- per-user custom quota wins absolutely
    (principal has customQuota
        && context.requestCount < principal.customQuota)
    // Rule 2 -- enterprise unlimited, only when no custom quota
    || (!(principal has customQuota)
        && principal.tier == "enterprise")
    // Rule 3 -- tier defaults, only when no custom quota and not enterprise
    || (!(principal has customQuota)
        && principal.tier == "free"
        && context.requestCount < 10)
    || (!(principal has customQuota)
        && principal.tier == "pro"
        && context.requestCount < 100)
};
