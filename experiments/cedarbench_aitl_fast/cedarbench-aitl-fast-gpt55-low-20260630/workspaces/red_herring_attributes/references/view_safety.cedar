// Ceiling: view permitted ONLY when (role in {reader, admin}) AND
// MFA verified AND principal == owner. Any candidate that permits
// outside this envelope -- e.g. by tying access to accountTier,
// department, or any other red-herring attribute -- violates this.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    (principal.role == "reader" || principal.role == "admin")
    && principal.mfaVerified
    && principal == resource.owner
};
