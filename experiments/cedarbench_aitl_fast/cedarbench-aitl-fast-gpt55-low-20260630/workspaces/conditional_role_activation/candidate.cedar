permit (
    principal is Employee,
    action == Action::"read",
    resource is SecureSystem
);

permit (
    principal is Employee,
    action == Action::"adminConfig",
    resource is SecureSystem
)
when {
    principal.homeRole == "admin" &&
    context.connectedFromOffice == true &&
    principal.officeNetworkAuth == true
};