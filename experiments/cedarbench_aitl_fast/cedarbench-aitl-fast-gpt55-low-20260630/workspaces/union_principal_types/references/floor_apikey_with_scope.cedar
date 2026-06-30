// Floor for ApiKey branch: any ApiKey whose scopes contain "api_call"
// MUST be permitted.
permit (
    principal is ApiKey,
    action == Action::"callApi",
    resource is Resource
)
when {
    principal.scopes.contains("api_call")
};
