permit (
    principal is User,
    action == Action::"collect",
    resource is DataPoint
)
when {
    resource.category == "anonymous"
};

permit (
    principal is User,
    action == Action::"collect",
    resource is DataPoint
)
when {
    (resource.category == "personal" ||
     resource.category == "behavioral" ||
     resource.category == "geolocation") &&
    context.now.durationSince(principal.dateOfBirth) >= duration("4748d")
};

permit (
    principal is User,
    action == Action::"collect",
    resource is DataPoint
)
when {
    (resource.category == "personal" ||
     resource.category == "behavioral" ||
     resource.category == "geolocation") &&
    context.now.durationSince(principal.dateOfBirth) < duration("4748d") &&
    context has parentalConsentToken
};

permit (
    principal is User,
    action == Action::"share",
    resource is DataPoint
)
when {
    resource.category == "anonymous"
};

permit (
    principal is User,
    action == Action::"share",
    resource is DataPoint
)
when {
    (resource.category == "behavioral" ||
     resource.category == "geolocation") &&
    context.now.durationSince(resource.owner.dateOfBirth) >= duration("4748d")
};

permit (
    principal is User,
    action == Action::"delete",
    resource is DataPoint
)
when {
    principal == resource.owner
};