permit (
    principal is User,
    action == Action::"grantAccessReservation",
    resource is Reservation
) when {
    resource in principal.hotelAdminPermissions ||
    resource in principal.propertyAdminPermissions
};