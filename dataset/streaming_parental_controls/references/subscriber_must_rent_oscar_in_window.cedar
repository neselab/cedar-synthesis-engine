// Floor: Subscriber MUST be permitted to rent any Oscar-nominated Movie
// when now is within `[2025-02-01T00:00:00Z, 2025-03-31T23:59:59Z]`.
permit (
    principal is Subscriber,
    action == Action::"rent",
    resource is Movie
)
when {
    resource.isOscarNominated
    && context.now.datetime >= datetime("2025-02-01T00:00:00Z")
    && context.now.datetime <= datetime("2025-03-31T23:59:59Z")
};
