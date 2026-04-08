// Ceiling: Subscriber may watch a Movie only when NOT (isKid AND rating is
// not "G" and not "PG"). Equivalently: if the kid profile is enabled, the
// movie's rating must be "G" or "PG".
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !(principal.profile.isKid
      && resource.rating != "G"
      && resource.rating != "PG")
};
