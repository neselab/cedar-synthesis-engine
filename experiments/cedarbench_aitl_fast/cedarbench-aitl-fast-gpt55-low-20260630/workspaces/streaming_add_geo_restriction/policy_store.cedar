// Policy store — verified policies appended here

// --- Verified (eval iteration 2) ---
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

forbid (
    principal,
    action == Action::"watch",
    resource
)
when {
    !resource.allowedRegions.contains(context.region)
};

permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree == true
};

permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isFree == true
};

permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.needsRentOrBuy == false &&
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h")
       || context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")))
};

permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    (
        resource.isEarlyAccess == false ||
        (
            principal.subscription.tier == "premium" &&
            context.now.datetime >= resource.releaseDate.offset(duration("-24h"))
        )
    ) &&
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h")
       || context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")))
};

permit (
    principal is Subscriber,
    action == Action::"rent",
    resource is Movie
)
when {
    resource.isOscarNominated == true &&
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime <= datetime("2025-03-31T23:59:59Z")
};

permit (
    principal is Subscriber,
    action == Action::"buy",
    resource is Movie
)
when {
    resource.isOscarNominated == true &&
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime <= datetime("2025-03-31T23:59:59Z")
};
