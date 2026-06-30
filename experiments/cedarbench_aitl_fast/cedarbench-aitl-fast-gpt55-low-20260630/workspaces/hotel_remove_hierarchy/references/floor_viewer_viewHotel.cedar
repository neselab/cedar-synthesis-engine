permit (
    principal is User,
    action == Action::"viewHotel",
    resource is Hotel
) when {
    resource in principal.viewPermissions.hotelReservations
};