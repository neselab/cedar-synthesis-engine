permit (
    principal is User,
    action == Action::"createReservation",
    resource is Property
) when {
    resource in principal.hotelAdminPermissions ||
    resource in principal.propertyAdminPermissions
};