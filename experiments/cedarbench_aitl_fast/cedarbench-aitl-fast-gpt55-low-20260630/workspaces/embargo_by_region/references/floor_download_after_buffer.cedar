// Floor: any user MUST be permitted to download an asset once the
// current time is at or after the per-region release datetime PLUS
// the 24-hour anti-leak buffer. Encodes the post-buffer permit
// requirement for all three regions.
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
