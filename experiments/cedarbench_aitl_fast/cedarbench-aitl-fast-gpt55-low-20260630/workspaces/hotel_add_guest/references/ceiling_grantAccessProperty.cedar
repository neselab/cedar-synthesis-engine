permit (
    principal is User,
    action == Action::"grantAccessProperty",
    resource is Property
) when {
    resource in principal.hotelAdminPermissions ||
    resource in principal.propertyAdminPermissions
};