// Ceiling: any moderator can escalate (no restriction).
permit (
    principal is Moderator,
    action == Action::"escalate",
    resource is ContentReport
);
