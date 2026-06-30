// Ceiling: Subscriber may rent a Movie only when isOscarNominated AND
// now in `[2025-02-01T00:00:00Z, 2025-03-31T23:59:59Z]` (per the spec).
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
