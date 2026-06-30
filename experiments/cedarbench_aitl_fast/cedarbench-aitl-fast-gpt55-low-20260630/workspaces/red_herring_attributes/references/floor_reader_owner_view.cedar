// Floor: a "reader" with MFA verified who owns the document MUST be
// able to view it. A candidate that adds extra gating on red-herring
// attributes (e.g. requiring accountTier == "pro" or a particular
// department) will block this floor and fail the check.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal.role == "reader"
    && principal.mfaVerified
    && principal == resource.owner
};
