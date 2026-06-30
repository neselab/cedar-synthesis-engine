// Ceiling: cancelReservation — members or admins only (not viewers)
permit (
    principal is User,
    action == Action::"cancelReservation",
    resource is Reservation
) when {
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.memberPermissions.propertyReservations ||
    resource in principal.hotelAdminPermissions ||
    resource in principal.propertyAdminPermissions
};
