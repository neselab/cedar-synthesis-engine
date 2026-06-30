permit (
    principal is Guest,
    action == Action::"guestViewReservation",
    resource is Reservation
) when {
    resource in principal.reservations
};