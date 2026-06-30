// Floor: members with hotelReservations MUST be able to cancel
permit (
    principal is User,
    action == Action::"cancelReservation",
    resource is Reservation
) when {
    resource in principal.memberPermissions.hotelReservations
};
