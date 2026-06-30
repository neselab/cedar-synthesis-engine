// Ceiling: a Subscriber may rent a Movie only when the movie is
// Oscar-nominated AND the request datetime falls within the Oscars window
// `[2025-02-02T00:00:00Z, 2025-03-02T23:59:59Z]`. The window is the 28-day
// period leading up to the 97th Academy Awards on March 2, 2025.
permit (
    principal is Subscriber,
    action == Action::"rent",
    resource is Movie
)
when {
    resource.isOscarNominated
    && context.now.datetime >= datetime("2025-02-02T00:00:00Z")
    && context.now.datetime <= datetime("2025-03-02T23:59:59Z")
};
