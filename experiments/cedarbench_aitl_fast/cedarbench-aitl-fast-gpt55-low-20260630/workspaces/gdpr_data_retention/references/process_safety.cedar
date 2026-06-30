// Ceiling: process only when processor AND active record.
permit (
    principal is User,
    action == Action::"process",
    resource is DataRecord
)
when {
    principal.role == "processor"
    && resource.retentionExpiry > context.now
    && resource.erasureRequested == false
};
