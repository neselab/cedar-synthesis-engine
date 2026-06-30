// Floor: an admin with an explicit grant MUST be able to `view` any
// document. Without this floor, "admins typically have access" would
// be vacuous under the most-restrictive reading. The candidate must
// be AT LEAST as permissive as this.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal.role == "admin"
    && principal.explicitGrant
};
