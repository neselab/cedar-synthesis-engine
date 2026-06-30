permit (
  principal,
  action == Action::"watch",
  resource
)
when {
  principal is FreeMember &&
  resource.isFree == true
};

permit (
  principal,
  action == Action::"watch",
  resource
)
when {
  principal is Subscriber &&
  resource is Movie &&
  resource.needsRentOrBuy == false &&
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
  resource.isEarlyAccess == false &&
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
  resource.isEarlyAccess == true &&
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
  resource.isOscarNominated == true &&
  context.now.datetime >= datetime("2025-02-02T00:00:00Z") &&
  context.now.datetime <= datetime("2025-03-02T23:59:59Z")
};

permit (
  principal,
  action == Action::"buy",
  resource
)
when {
  principal is Subscriber &&
  resource is Movie &&
  resource.isOscarNominated == true &&
  context.now.datetime >= datetime("2025-02-02T00:00:00Z") &&
  context.now.datetime <= datetime("2025-03-02T23:59:59Z")
};

forbid (
  principal is Subscriber,
  action == Action::"watch",
  resource
)
when {
  principal.profile.isKid == true &&
  (
    context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h") ||
    context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")
  )
};