// Ceiling: resolve under same threshold as review.
permit (
    principal is Moderator,
    action == Action::"resolve",
    resource is ContentReport
)
when {
    (principal.trustLevel >= 1 && resource.severity <= 2)
    || (principal.trustLevel >= 2 && resource.severity <= 4)
    || principal.trustLevel >= 3
};
