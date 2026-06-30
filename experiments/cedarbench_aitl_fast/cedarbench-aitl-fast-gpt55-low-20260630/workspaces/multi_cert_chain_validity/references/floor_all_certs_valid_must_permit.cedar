// Floor: when all three certificate chains are simultaneously valid at
// context.now, secure access MUST be permitted. This is the central
// positive assertion -- the candidate cannot be over-restrictive.
permit (
    principal is User,
    action == Action::"accessSecure",
    resource is Resource
)
when {
    context.now >= principal.userCertValidFrom
    && context.now <= principal.userCertValidUntil
    && context.now >= context.userOrg.orgCertValidFrom
    && context.now <= context.userOrg.orgCertValidUntil
    && context.now >= resource.requiredCa.caCertValidFrom
    && context.now <= resource.requiredCa.caCertValidUntil
};
