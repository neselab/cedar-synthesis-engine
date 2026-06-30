// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"accessSecure",
    resource is Resource
)
when {
    context.now >= principal.userCertValidFrom &&
    context.now <= principal.userCertValidUntil &&
    context.now >= context.userOrg.orgCertValidFrom &&
    context.now <= context.userOrg.orgCertValidUntil &&
    context.now >= resource.requiredCa.caCertValidFrom &&
    context.now <= resource.requiredCa.caCertValidUntil
};
