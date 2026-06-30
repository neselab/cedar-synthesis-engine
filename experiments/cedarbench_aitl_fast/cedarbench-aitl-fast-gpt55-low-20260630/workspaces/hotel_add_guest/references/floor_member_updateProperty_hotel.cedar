permit (
    principal is User,
    action == Action::"updateProperty",
    resource is Property
) when {
    resource in principal.memberPermissions.hotelReservations
};