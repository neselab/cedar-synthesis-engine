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
    !resource.needsRentOrBuy
};

permit (
    principal,
    action == Action::"watch",
    resource
)
when {
    principal is Subscriber &&
    resource is Show &&
    (
        !resource.isEarlyAccess ||
        context.now.datetime >= resource.releaseDate ||
        (
            principal.subscription.tier == "premium" &&
            context.now.datetime >= resource.releaseDate.offset(duration("-24h"))
        )
    )
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