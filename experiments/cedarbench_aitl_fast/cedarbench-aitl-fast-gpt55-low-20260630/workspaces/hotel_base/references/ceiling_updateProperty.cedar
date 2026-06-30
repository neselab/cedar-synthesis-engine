permit (
    principal is User,
    action == Action::"updateProperty",
    resource is Property
) when {
    resource in principal.memberPermissions.propertyReservations ||
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.propertyAdminPermissions ||
    resource in principal.hotelAdminPermissions
};