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
        context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h") ||
        context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")
    )
};

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
    principal is TrialMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree
};

permit (
    principal is TrialMember,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isFree
};

permit (
    principal is TrialMember,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.isFree &&
    !resource.needsRentOrBuy &&
    context.now.datetime < principal.trialExpiry
};

permit (
    principal is TrialMember,
    action == Action::"watch",
    resource is Show
)
when {
    !resource.isFree &&
    !resource.isEarlyAccess &&
    context.now.datetime < principal.trialExpiry
};

permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.needsRentOrBuy &&
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
    !resource.isEarlyAccess &&
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
    resource.isEarlyAccess &&
    principal.subscription.tier == "premium" &&
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
    resource.isOscarNominated &&
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime <= datetime("2025-03-31T23:59:59Z")
};

permit (
    principal is Subscriber,
    action == Action::"buy",
    resource is Movie
)
when {
    resource.isOscarNominated &&
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime <= datetime("2025-03-31T23:59:59Z")
};
