// Floor: FreeMember MUST watch any free Movie. FreeMember has no profile,
// so the parental rating forbid does not apply (Cedar would type-error if a
// forbid tried `principal.profile.maxRating` without an `is Subscriber`
// guard). No §8.8 exclusion needed.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree
};
