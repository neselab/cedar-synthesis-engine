// Ceiling: Subscriber may watch a Movie only when the movie's rating does
// not exceed the profile's maxRating in the hierarchy G < PG < PG13 < R.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    principal.profile.maxRating == "R"
    || (principal.profile.maxRating == "PG13"
        && (resource.rating == "G" || resource.rating == "PG" || resource.rating == "PG13"))
    || (principal.profile.maxRating == "PG"
        && (resource.rating == "G" || resource.rating == "PG"))
    || (principal.profile.maxRating == "G" && resource.rating == "G")
};
