// Ceiling: Subscriber may watch a Show only when the show's rating does
// not exceed the profile's maxRating per the hierarchy G < PG < PG13 < R.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    principal.profile.maxRating == "R"
    || (principal.profile.maxRating == "PG13"
        && (resource.rating == "G" || resource.rating == "PG" || resource.rating == "PG13"))
    || (principal.profile.maxRating == "PG"
        && (resource.rating == "G" || resource.rating == "PG"))
    || (principal.profile.maxRating == "G" && resource.rating == "G")
};
