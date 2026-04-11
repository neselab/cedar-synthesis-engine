// Floor: Subscriber MUST be permitted to watch any Movie that does not require
// rent-or-buy. There is no bedtime forbid in this scenario, so no §8.8
// floor-bound consistency exclusion is needed.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.needsRentOrBuy
};
