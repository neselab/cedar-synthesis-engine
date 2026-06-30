permit (
    principal is User,
    action == Action::"viewProperty",
    resource is Property
) when {
    resource in principal.viewPermissions.propertyReservations ||
    resource in principal.viewPermissions.hotelReservations ||
    resource in principal.memberPermissions.propertyReservations ||
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.propertyAdminPermissions ||
    resource in principal.hotelAdminPermissions
};