// Floor: an admin Employee with the office-network authorization flag,
// connecting from the office network, MUST be permitted to perform
// adminConfig on a SecureSystem.
permit (
    principal is Employee,
    action == Action::"adminConfig",
    resource is SecureSystem
)
when {
    principal.homeRole == "admin"
    && context.connectedFromOffice == true
    && principal.officeNetworkAuth == true
};
