// Ceiling: Subscriber may watch a Movie only when it does not require rent-or-buy.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.needsRentOrBuy
};
