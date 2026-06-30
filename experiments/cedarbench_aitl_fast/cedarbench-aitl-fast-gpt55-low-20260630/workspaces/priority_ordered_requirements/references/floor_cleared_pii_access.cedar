// Floor: a user with pii_clearance MUST access a non-legal-hold PII
// record (R2 fires). legalHold pinned to false to dodge R1.
permit (
    principal is User,
    action == Action::"access",
    resource is Record
)
when {
    !resource.legalHold
    && resource.containsPII
    && principal.pii_clearance
};
