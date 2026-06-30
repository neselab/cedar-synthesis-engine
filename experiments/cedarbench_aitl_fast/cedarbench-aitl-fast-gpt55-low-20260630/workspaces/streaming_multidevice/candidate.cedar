permit (
    principal,
    action == Action::"watch",
    resource
)
when {
    principal is FreeMember &&
    resource is Movie &&
    resource.isFree
};

permit (
    principal,
    action == Action::"watch",
    resource
)
when {
    principal is FreeMember &&
    resource is Show &&
    resource.isFree
};

permit (
    principal,
    action == Action::"watch",
    resource
)
when {
    principal is Subscriber &&
    resource is Movie &&
    !resource.needsRentOrBuy &&
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h") ||
       context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")))
};

permit (
    principal,
    action == Action::"watch",
    resource
)
when {
    principal is Subscriber &&
    resource is Show &&
    !resource.isEarlyAccess &&
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h") ||
       context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")))
};

permit (
    principal,
    action == Action::"watch",
    resource
)
when {
    principal is Subscriber &&
    resource is Show &&
    principal.subscription.tier == "premium" &&
    resource.isEarlyAccess &&
    context.now.datetime >= resource.releaseDate.offset(duration("-24h")) &&
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h") ||
       context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")))
};

permit (
    principal,
    action == Action::"rent",
    resource
)
when {
    principal is Subscriber &&
    resource is Movie &&
    resource.isOscarNominated &&
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime <= datetime("2025-03-31T23:59:59Z")
};

permit (
    principal,
    action == Action::"buy",
    resource
)
when {
    principal is Subscriber &&
    resource is Movie &&
    resource.isOscarNominated &&
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime <= datetime("2025-03-31T23:59:59Z")
};

forbid (
    principal,
    action == Action::"watch",
    resource
)
when {
    principal is Subscriber &&
    principal.profile.isKid &&
    (
        context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h") ||
        context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")
    )
};

forbid (
    principal,
    action == Action::"watch",
    resource
)
when {
    principal is FreeMember &&
    context.activeStreams >= 1
};

forbid (
    principal,
    action == Action::"watch",
    resource
)
when {
    principal is Subscriber &&
    principal.subscription.tier == "standard" &&
    context.activeStreams >= 2
};

forbid (
    principal,
    action == Action::"watch",
    resource
)
when {
    principal is Subscriber &&
    principal.subscription.tier == "premium" &&
    context.activeStreams >= 5
};