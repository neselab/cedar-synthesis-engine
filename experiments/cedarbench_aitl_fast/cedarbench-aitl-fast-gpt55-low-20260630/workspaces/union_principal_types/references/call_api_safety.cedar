// Ceiling for callApi: must be one of the three permitted branches.
// Combined ceiling — candidate ⇒ reference. The candidate may be no
// more permissive than the disjunction of the three legitimate cases.
permit (
    principal,
    action == Action::"callApi",
    resource is Resource
)
when {
    (principal is User && principal.mfaVerified)
    || (principal is ApiKey && principal.scopes.contains("api_call"))
    || (principal is ServiceAccount && principal.serviceName != "")
};
