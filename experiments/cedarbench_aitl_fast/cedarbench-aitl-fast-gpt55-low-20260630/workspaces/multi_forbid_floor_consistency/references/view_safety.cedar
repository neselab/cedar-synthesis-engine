// Ceiling for `view`: only forbids 1 (suspension) and 3 (classified
// without MFA) apply. Forbids 2 (outside hours) and 4 (approval) do
// NOT apply to `view`.
permit (
    principal is User,
    action == Action::"view",
    resource is Resource
)
when {
    !principal.isSuspended
    && (!resource.isClassified || principal.mfaVerified)
};
