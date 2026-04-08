// Ceiling: Subscriber may watch a Show only when NOT (isKid AND rating is
// not "G" and not "PG"). Kid profiles can only watch G or PG shows.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    !(principal.profile.isKid
      && resource.rating != "G"
      && resource.rating != "PG")
};
