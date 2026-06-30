permit (
    principal is User,
    action == Action::"viewFranchise",
    resource is Franchise
)
when {
    resource in principal.viewPermissions.franchiseReservations ||
    resource in principal.memberPermissions.franchiseReservations ||
    resource in principal.franchiseAdminPermissions
};