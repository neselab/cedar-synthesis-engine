// Ceiling: a Subscriber may watch a Show only when it is NOT the case that
// (a) the kid profile is enabled AND (b) the local clock time is in the
// bedtime window (>= 21:00 or < 06:00).
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h")
       || context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")))
};
