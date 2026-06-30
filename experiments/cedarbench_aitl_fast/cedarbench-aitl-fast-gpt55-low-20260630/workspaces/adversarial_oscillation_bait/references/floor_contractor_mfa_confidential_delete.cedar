// FLOOR_CONTRACTOR_MFA_CONFIDENTIAL for `delete`.
permit (
    principal is User,
    action == Action::"delete",
    resource is Resource
)
when {
    principal.role == "user"
    && principal.isContractor == true
    && resource.classification == "confidential"
    && context.mfaVerified == true
};
