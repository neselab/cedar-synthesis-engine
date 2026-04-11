// Ceiling: Subscriber may watch a Movie only when NOT (isKid AND localTime in bedtime window).
// Bedtime window is local-time-of-day < 06:00 OR >= 21:00.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h")
       || context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")))
};
