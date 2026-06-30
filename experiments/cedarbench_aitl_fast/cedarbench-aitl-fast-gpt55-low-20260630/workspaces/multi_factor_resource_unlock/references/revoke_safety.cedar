// Ceiling: revoke permitted only when admin with hasMfa AND
// hasManagerApproval, regardless of sensitivity level.
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
