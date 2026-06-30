// Floor: an admin with hasMfa AND hasManagerApproval MUST be able
// to revoke any secret (level is irrelevant for revoke).
permit (
    principal is User,
    action == Action::"revoke",
    resource is Secret
)
when {
    principal.role == "admin"
    && context.hasMfa
    && context.hasManagerApproval
};
