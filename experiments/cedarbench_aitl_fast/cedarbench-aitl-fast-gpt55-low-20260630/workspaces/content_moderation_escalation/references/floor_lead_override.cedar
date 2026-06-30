// Floor: lead mod MUST override.
permit (
    principal is Moderator,
    action == Action::"override",
    resource is ContentReport
)
when {
    principal.trustLevel >= 3
};
