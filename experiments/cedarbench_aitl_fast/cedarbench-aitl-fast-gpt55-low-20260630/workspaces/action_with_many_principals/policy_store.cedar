// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"invoke",
    resource is Resource
)
when {
    principal.mfaVerified == true
};

permit (
    principal is ApiKey,
    action == Action::"invoke",
    resource is Resource
)
when {
    principal.scopes.contains("invoke")
};

permit (
    principal is ServiceAccount,
    action == Action::"invoke",
    resource is Resource
)
when {
    principal.serviceName != ""
};

permit (
    principal is Webhook,
    action == Action::"invoke",
    resource is Resource
)
when {
    principal.signatureValid == true
};

permit (
    principal is BatchJob,
    action == Action::"invoke",
    resource is Resource
);

permit (
    principal is Scheduler,
    action == Action::"invoke",
    resource is Resource
)
when {
    principal.cronVerified == true
};
