permit (
    principal is User,
    action == Action::"viewReservation",
    resource is Reservation
) when {
    resource in principal.viewPermissions.hotelReservations ||
    resource in principal.viewPermissions.propertyReservations ||
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.memberPermissions.propertyReservations ||
    resource in principal.hotelAdminPermissions ||
    resource in principal.propertyAdminPermissions
};