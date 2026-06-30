permit (
    principal is User,
    action == Action::"updateFranchise",
    resource is Franchise
) when {
    resource in principal.memberPermissions.franchiseReservations
};