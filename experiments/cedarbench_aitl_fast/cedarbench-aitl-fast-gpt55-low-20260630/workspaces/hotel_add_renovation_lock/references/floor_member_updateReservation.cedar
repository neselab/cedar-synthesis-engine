permit (
    principal is User,
    action == Action::"updateReservation",
    resource is Reservation
) when {
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.memberPermissions.propertyReservations
};