// Ceiling: secure access is permitted ONLY when all three certificate
// chains are simultaneously valid at context.now. Six comparisons in
// conjunction: each certificate's validFrom <= now <= validUntil.
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
