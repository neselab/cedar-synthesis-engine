// Floor: processor MUST read active records.
permit (
    principal is User,
    action == Action::"read",
    resource is DataRecord
)
when {
    principal.role == "processor"
    && resource.retentionExpiry > context.now
    && resource.erasureRequested == false
};
