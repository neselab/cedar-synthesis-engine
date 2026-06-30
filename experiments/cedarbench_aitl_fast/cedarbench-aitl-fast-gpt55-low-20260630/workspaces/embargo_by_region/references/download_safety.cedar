// Ceiling: download permitted only when the current time is at or
// after the release datetime for the user's region PLUS a 24-hour
// anti-leak buffer. Cedar has no dynamic record key access -- the
// policy must branch explicitly on each region value.
permit (
    principal is User,
    action == Action::"download",
    resource is Asset
)
when {
    (principal.region == "us"   && context.now >= resource.releaseUS.offset(duration("24h")))
    || (principal.region == "eu"   && context.now >= resource.releaseEU.offset(duration("24h")))
    || (principal.region == "apac" && context.now >= resource.releaseAPAC.offset(duration("24h")))
};
