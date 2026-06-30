permit (
    principal is User,
    action == Action::"createHotel",
    resource is Hotel
) when {
    resource in principal.memberPermissions.franchiseReservations ||
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.franchiseAdminPermissions ||
    resource in principal.hotelAdminPermissions
};