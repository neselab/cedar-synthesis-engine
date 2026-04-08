// Ceiling: Subscriber may watch a Show only when at least one of:
//  (a) the show is not in early access, OR
//  (b) the current time is at or past the show's release date, OR
//  (c) the subscriber is on the premium tier AND now is within 24h before release.
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
