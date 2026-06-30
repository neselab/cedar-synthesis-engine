permit (
    principal is User,
    action == Action::"createProperty",
    resource is Hotel
) when {
    resource in principal.memberPermissions.hotelReservations ||
    resource in principal.hotelAdminPermissions
};