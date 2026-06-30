// Ceiling: override only when lead (trustLevel >= 3).
permit (
    principal is Moderator,
    action == Action::"override",
    resource is ContentReport
)
when {
    principal.trustLevel >= 3
};
