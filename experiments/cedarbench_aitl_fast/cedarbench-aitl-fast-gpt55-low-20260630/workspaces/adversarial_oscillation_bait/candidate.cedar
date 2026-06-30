permit (
    principal is User,
    action in [Action::"read", Action::"write", Action::"delete"],
    resource is Resource
)
when {
    principal.role == "admin"
};

permit (
    principal is User,
    action in [Action::"read", Action::"write", Action::"delete"],
    resource is Resource
)
when {
    principal == resource.owner &&
    (
        resource.classification != "confidential" ||
        context.mfaVerified == true
    )
};

permit (
    principal is User,
    action in [Action::"read", Action::"write", Action::"delete"],
    resource is Resource
)
when {
    principal.role == "user" &&
    principal.isContractor == false &&
    resource.classification != "confidential"
};

permit (
    principal is User,
    action in [Action::"read", Action::"write", Action::"delete"],
    resource is Resource
)
when {
    principal.role == "user" &&
    principal.isContractor == true &&
    resource.classification == "confidential" &&
    context.mfaVerified == true
};