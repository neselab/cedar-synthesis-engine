// Floor (precedence test): when BOTH legal hold AND PII apply, R1 wins.
// A legal_team user MUST still access the record — even without
// pii_clearance — proving R1 strictly dominates R2.
permit (
    principal is User,
    action == Action::"access",
    resource is Record
)
when {
    resource.legalHold
    && resource.containsPII
    && principal.role == "legal_team"
    && !principal.pii_clearance
};
