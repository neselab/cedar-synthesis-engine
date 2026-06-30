// Ceiling: Subscriber may rent a Movie only when the movie is Oscar-nominated
// AND the current time is within the Oscar promo window
// `[2025-02-01T00:00:00Z, 2025-03-31T23:59:59Z]` (the entire February-March
// 2025 window per the spec).
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
