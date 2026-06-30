// Floor: an "admin" with MFA verified who owns the document MUST be
// able to view it. Admins still require ownership -- no super-admin
// override exists. A candidate that adds gating on any red-herring
// attribute will block this floor and fail the check.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal.role == "admin"
    && principal.mfaVerified
    && principal == resource.owner
};
