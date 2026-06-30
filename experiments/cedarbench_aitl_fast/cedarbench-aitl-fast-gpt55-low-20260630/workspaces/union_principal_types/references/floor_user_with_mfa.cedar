// Floor for User branch: any User with mfaVerified MUST be permitted.
permit (
    principal is User,
    action == Action::"callApi",
    resource is Resource
)
when {
    principal.mfaVerified
};
