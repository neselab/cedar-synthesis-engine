permit (
    principal is User,
    action == Action::"viewReservation",
    resource is Reservation
)
when {
    resource in principal.viewPermissions.propertyReservations
};