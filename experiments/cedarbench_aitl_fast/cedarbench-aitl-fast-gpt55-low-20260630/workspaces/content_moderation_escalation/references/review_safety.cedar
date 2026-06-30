// Ceiling: review only when trust level meets severity threshold.
permit (
    principal is Moderator,
    action == Action::"review",
    resource is ContentReport
)
when {
    (principal.trustLevel >= 1 && resource.severity <= 2)
    || (principal.trustLevel >= 2 && resource.severity <= 4)
    || principal.trustLevel >= 3
};
