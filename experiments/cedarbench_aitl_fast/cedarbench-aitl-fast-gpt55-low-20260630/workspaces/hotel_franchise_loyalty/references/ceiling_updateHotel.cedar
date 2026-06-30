permit (
    principal is User,
    action == Action::"updateHotel",
    resource is Hotel
)
when {
    resource in principal.memberPermissions.franchiseReservations ||
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.franchiseAdminPermissions ||
    resource in principal.hotelAdminPermissions
};