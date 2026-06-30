permit (
    principal is User,
    action == Action::"grantAccessReservation",
    resource is Reservation
) when {
    resource in principal.propertyAdminPermissions ||
    resource in principal.hotelAdminPermissions
};