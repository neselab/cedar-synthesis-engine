// Ceiling: Subscriber may watch a Show only when NOT (isKid AND localTime in bedtime window).
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
