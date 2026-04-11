// Ceiling: Subscriber may watch a Movie only when !needsRentOrBuy.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.needsRentOrBuy
};
