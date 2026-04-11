// Floor: a legal team member MUST be permitted to edit a document that
// is under a legal hold, REGARDLESS of the expiry date. This is the
// central override: legal hold preserves edit access past expiry.
permit (
    principal is User,
    action == Action::"editDocument",
    resource is Document
)
when {
    principal.isLegalTeam && resource.legalHold
};
