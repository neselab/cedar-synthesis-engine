// Ceiling: a Subscriber may watch a Movie only when the movie does not
// require rent-or-buy. (Movies that require rent-or-buy must be paid for
// separately via the rent/buy actions, not via the watch action.)
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.needsRentOrBuy
};
