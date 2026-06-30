// Floor for ServiceAccount branch: any ServiceAccount with non-empty
// serviceName MUST be permitted.
permit (
    principal is ServiceAccount,
    action == Action::"callApi",
    resource is Resource
)
when {
    principal.serviceName != ""
};
