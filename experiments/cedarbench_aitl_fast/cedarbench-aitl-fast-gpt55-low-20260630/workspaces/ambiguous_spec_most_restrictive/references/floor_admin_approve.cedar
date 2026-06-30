// Floor: an admin with an explicit grant MUST be able to `approve`
// any document. Without this floor, "certain privileged users can
// perform approvals" would be vacuous under the most-restrictive
// reading. The candidate must be AT LEAST as permissive as this.
permit (
    principal is User,
    action == Action::"approve",
    resource is Document
)
when {
    principal.role == "admin"
    && principal.explicitGrant
};
