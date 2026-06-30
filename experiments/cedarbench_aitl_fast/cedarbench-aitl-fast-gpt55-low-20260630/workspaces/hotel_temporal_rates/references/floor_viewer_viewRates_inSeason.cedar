permit (
    principal is User,
    action == Action::"viewRates",
    resource is Property
) when {
    resource in principal.viewPermissions.hotelReservations &&
    context.currentTime >= resource.seasonStart &&
    context.currentTime <= resource.seasonEnd
};