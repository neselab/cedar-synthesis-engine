// Floor: a Subscriber MUST be permitted to rent a Movie when the movie is
// Oscar-nominated AND the request datetime is in the Oscars window
// `[2025-02-02T00:00:00Z, 2025-03-02T23:59:59Z]`. There are no global
// forbids on the rent action, so no §8.8 exclusions are needed in the
// floor's when clause.
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
