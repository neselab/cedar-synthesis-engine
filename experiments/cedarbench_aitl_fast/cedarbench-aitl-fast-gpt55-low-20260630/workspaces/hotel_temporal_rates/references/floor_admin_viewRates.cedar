permit (
    principal is User,
    action == Action::"viewRates",
    resource is Property
) when {
    resource in principal.hotelAdminPermissions
};