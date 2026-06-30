// FLOOR_CONTRACTOR_MFA_CONFIDENTIAL for `read`. A user-role
// contractor with MFA verified MUST read confidential resources.
// This is the §8.6 trap target: a forbid `when isContractor &&
// classification == "confidential"` would block this floor.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal.role == "user"
    && principal.isContractor == true
    && resource.classification == "confidential"
    && context.mfaVerified == true
};
