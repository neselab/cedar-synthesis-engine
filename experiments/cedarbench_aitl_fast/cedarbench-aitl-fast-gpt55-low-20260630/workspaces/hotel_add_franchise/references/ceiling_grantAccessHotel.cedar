permit (
    principal is User,
    action == Action::"grantAccessHotel",
    resource is Hotel
) when {
    resource in principal.franchiseAdminPermissions ||
    resource in principal.hotelAdminPermissions
};