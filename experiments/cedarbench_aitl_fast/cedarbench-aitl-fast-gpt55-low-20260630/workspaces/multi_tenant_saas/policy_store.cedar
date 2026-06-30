// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action in [Action::"readResource", Action::"writeResource", Action::"deleteResource"],
    resource is Resource
)
when {
    principal.tenant == resource.tenant
};

permit (
    principal is User,
    action == Action::"readResource",
    resource is Resource
)
when {
    principal.isGlobalSupport == true &&
    context.supportSessionActive == true &&
    context.ticketId != ""
};
