permit (
    principal is User,
    action == Action::"viewRates",
    resource is Property
) when {
    (resource in principal.viewPermissions.hotelReservations ||
     resource in principal.viewPermissions.propertyReservations ||
     resource in principal.memberPermissions.hotelReservations ||
     resource in principal.memberPermissions.propertyReservations ||
     resource in principal.hotelAdminPermissions ||
     resource in principal.propertyAdminPermissions) &&
    (context.currentTime >= resource.seasonStart && context.currentTime <= resource.seasonEnd ||
     resource in principal.hotelAdminPermissions ||
     resource in principal.propertyAdminPermissions)
};