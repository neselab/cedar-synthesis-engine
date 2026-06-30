// Floor: when context.now is strictly in the INTERIOR of every cert
// validity window (strictly greater than every validFrom, strictly less
// than every validUntil), secure access MUST be permitted. This is a
// stronger positive witness that catches off-by-one direction errors:
// the strict-interior case still implies the inclusive ceiling.
permit (
    principal is User,
    action == Action::"accessSecure",
    resource is Resource
)
when {
    context.now > principal.userCertValidFrom
    && context.now < principal.userCertValidUntil
    && context.now > context.userOrg.orgCertValidFrom
    && context.now < context.userOrg.orgCertValidUntil
    && context.now > resource.requiredCa.caCertValidFrom
    && context.now < resource.requiredCa.caCertValidUntil
};
