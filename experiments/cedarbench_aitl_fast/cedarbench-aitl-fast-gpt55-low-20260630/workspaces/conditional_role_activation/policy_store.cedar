// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
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
