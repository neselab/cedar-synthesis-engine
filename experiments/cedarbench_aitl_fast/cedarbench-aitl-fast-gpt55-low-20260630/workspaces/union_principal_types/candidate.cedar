permit (
    principal,
    action == Action::"callApi",
    resource
)
when {
    resource is Resource &&
    (
        (principal is User && principal.mfaVerified == true) ||
        (principal is ApiKey && principal.scopes.contains("api_call")) ||
        (principal is ServiceAccount && principal.serviceName != "")
    )
};