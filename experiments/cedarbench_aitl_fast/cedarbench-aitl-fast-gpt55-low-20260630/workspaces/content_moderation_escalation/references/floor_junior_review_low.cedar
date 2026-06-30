// Floor: junior mod (trustLevel >= 1) MUST review severity <= 2.
permit (
    principal is Moderator,
    action == Action::"review",
    resource is ContentReport
)
when {
    principal.trustLevel >= 1
    && resource.severity <= 2
};
