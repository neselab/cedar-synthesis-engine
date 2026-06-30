// FLOOR_CONTRACTOR_MFA_CONFIDENTIAL for `write`.
permit (
    principal is User,
    action == Action::"write",
    resource is Resource
)
when {
    principal.role == "user"
    && principal.isContractor == true
    && resource.classification == "confidential"
    && context.mfaVerified == true
};
