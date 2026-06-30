permit (
    principal is User,
    action == Action::"grantAccessFranchise",
    resource is Franchise
)
when {
    resource in principal.franchiseAdminPermissions
};