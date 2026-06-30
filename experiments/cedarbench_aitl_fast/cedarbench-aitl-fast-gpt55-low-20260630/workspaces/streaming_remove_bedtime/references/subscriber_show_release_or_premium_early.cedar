// Ceiling: Subscriber may watch a Show only when at least one of these holds:
//  (a) the show is not in early access at all, OR
//  (b) the current time is at or past the show's release date, OR
//  (c) the subscriber is on the premium tier AND the current time is within
//      the 24-hour window before the release date.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    !resource.isEarlyAccess
    || context.now.datetime >= resource.releaseDate
    || (principal.subscription.tier == "premium"
        && context.now.datetime >= resource.releaseDate.offset(duration("-24h")))
};
