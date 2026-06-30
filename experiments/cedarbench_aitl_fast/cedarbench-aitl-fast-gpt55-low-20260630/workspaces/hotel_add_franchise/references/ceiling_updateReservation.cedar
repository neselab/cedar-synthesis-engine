permit (
    principal is User,
    action == Action::"updateReservation",
    resource is Reservation
) when {
    resource in principal.memberPermissions.franchiseReservations ||
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.memberPermissions.propertyReservations ||
    resource in principal.franchiseAdminPermissions ||
    resource in principal.hotelAdminPermissions ||
    resource in principal.propertyAdminPermissions
};