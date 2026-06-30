// FLOOR_OWNER for `delete` with §8.8 carve-out.
permit (
    principal is User,
    action == Action::"delete",
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
