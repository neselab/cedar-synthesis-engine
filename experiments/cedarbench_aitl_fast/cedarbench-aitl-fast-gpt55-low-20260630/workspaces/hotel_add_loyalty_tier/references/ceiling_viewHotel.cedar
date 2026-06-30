permit (
    principal is User,
    action == Action::"viewHotel",
    resource is Hotel
) when {
    resource in principal.viewPermissions.hotelReservations ||
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.hotelAdminPermissions
};