permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree
};

permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isFree
};

permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.needsRentOrBuy &&
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h") ||
       context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")))
};

permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    (
        !resource.isEarlyAccess ||
        context.now.datetime >= resource.releaseDate ||
        (
            principal.subscription.tier == "premium" &&
            context.now.datetime >= resource.releaseDate.offset(duration("-24h"))
        )
    ) &&
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h") ||
       context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")))
};

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource
)
when {
    principal.profile.isKid &&
    (
        context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h") ||
        context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h")
    )
};