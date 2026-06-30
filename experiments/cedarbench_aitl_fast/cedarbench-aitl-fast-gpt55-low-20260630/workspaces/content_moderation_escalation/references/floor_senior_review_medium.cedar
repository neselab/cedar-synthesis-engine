// Floor: senior mod (trustLevel >= 2) MUST review severity <= 4.
permit (
    principal is Moderator,
    action == Action::"review",
    resource is ContentReport
)
when {
    principal.trustLevel >= 2
    && resource.severity <= 4
};
