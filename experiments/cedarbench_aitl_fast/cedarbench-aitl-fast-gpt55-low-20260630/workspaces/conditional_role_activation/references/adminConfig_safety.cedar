// Ceiling: adminConfig is permitted ONLY when the elevated admin role
// is active — that is, when all three activation conditions hold:
// homeRole is admin, the request is from the office network, and the
// employee has the office-network authorization flag.
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
