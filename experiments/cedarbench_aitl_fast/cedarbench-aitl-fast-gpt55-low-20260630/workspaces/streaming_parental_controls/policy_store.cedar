// Policy store — verified policies appended here

// --- Verified (eval iteration 2) ---
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
    (
        principal.profile.isKid == false ||
        (
            context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("6h") &&
            context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("21h")
        )
    ) &&
    (
        principal.profile.maxRating == "R" ||
        (principal.profile.maxRating == "PG13" &&
            (resource.rating == "G" || resource.rating == "PG" || resource.rating == "PG13")) ||
        (principal.profile.maxRating == "PG" &&
            (resource.rating == "G" || resource.rating == "PG")) ||
        (principal.profile.maxRating == "G" && resource.rating == "G")
    )
};

permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isEarlyAccess == false &&
    (
        principal.profile.isKid == false ||
        (
            context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("6h") &&
            context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("21h")
        )
    ) &&
    (
        principal.profile.maxRating == "R" ||
        (principal.profile.maxRating == "PG13" &&
            (resource.rating == "G" || resource.rating == "PG" || resource.rating == "PG13")) ||
        (principal.profile.maxRating == "PG" &&
            (resource.rating == "G" || resource.rating == "PG")) ||
        (principal.profile.maxRating == "G" && resource.rating == "G")
    )
};

permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    principal.subscription.tier == "premium" &&
    resource.isEarlyAccess == true &&
    context.now.datetime >= resource.releaseDate.offset(duration("-24h")) &&
    (
        principal.profile.isKid == false ||
        (
            context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("6h") &&
            context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("21h")
        )
    ) &&
    (
        principal.profile.maxRating == "R" ||
        (principal.profile.maxRating == "PG13" &&
            (resource.rating == "G" || resource.rating == "PG" || resource.rating == "PG13")) ||
        (principal.profile.maxRating == "PG" &&
            (resource.rating == "G" || resource.rating == "PG")) ||
        (principal.profile.maxRating == "G" && resource.rating == "G")
    )
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

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource
)
when {
    principal.profile.isKid == true &&
    (
        context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h") ||
        context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h")
    )
};

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !(
        principal.profile.maxRating == "R" ||
        (principal.profile.maxRating == "PG13" &&
            (resource.rating == "G" || resource.rating == "PG" || resource.rating == "PG13")) ||
        (principal.profile.maxRating == "PG" &&
            (resource.rating == "G" || resource.rating == "PG")) ||
        (principal.profile.maxRating == "G" && resource.rating == "G")
    )
};

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    !(
        principal.profile.maxRating == "R" ||
        (principal.profile.maxRating == "PG13" &&
            (resource.rating == "G" || resource.rating == "PG" || resource.rating == "PG13")) ||
        (principal.profile.maxRating == "PG" &&
            (resource.rating == "G" || resource.rating == "PG")) ||
        (principal.profile.maxRating == "G" && resource.rating == "G")
    )
};
