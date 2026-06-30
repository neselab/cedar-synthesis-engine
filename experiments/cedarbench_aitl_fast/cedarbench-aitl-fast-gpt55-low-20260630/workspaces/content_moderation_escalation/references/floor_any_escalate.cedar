// Floor: any moderator MUST escalate.
permit (
    principal is Moderator,
    action == Action::"escalate",
    resource is ContentReport
);
