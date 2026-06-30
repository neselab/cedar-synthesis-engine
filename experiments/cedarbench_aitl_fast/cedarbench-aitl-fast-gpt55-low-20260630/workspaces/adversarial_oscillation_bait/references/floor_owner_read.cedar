// FLOOR_OWNER for `read` with §8.8 carve-out: owner is permitted
// UNLESS the resource is confidential AND mfaVerified is false AND
// the principal is not admin. Equivalently, owner is permitted when:
//   role == "admin" OR classification != "confidential" OR mfaVerified.
// Without this carve-out, the floor would be inconsistent with the
// safety ceiling (an owner-contractor of a confidential resource
// without MFA would be a permit-floor point outside the ceiling).
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal == resource.owner
    && (
        principal.role == "admin"
        || resource.classification != "confidential"
        || context.mfaVerified
    )
};
