permit (
    principal is User,
    action == Action::"viewProperty",
    resource is Property
) when {
    resource in principal.viewPermissions.propertyReservations ||
    resource in principal.memberPermissions.propertyReservations ||
    resource in principal.propertyAdminPermissions
};