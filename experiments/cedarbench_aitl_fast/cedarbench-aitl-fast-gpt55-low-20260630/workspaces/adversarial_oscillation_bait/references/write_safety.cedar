// CEILING for `write`. Same structure as read_safety.
permit (
    principal is User,
    action == Action::"write",
    resource is Resource
)
when {
    principal.role == "admin"
    || (
        principal == resource.owner
        && (resource.classification != "confidential" || context.mfaVerified)
    )
    || (
        principal.role == "user"
        && principal.isContractor == false
        && resource.classification != "confidential"
    )
    || (
        principal.role == "user"
        && principal.isContractor == true
        && resource.classification == "confidential"
        && context.mfaVerified == true
    )
};
