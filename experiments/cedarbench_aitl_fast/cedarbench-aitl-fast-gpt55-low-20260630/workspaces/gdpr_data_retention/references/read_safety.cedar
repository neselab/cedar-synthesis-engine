// Ceiling: read only when active record (not expired, not erasure-flagged)
// AND role is processor/controller/dpo.
permit (
    principal is User,
    action == Action::"read",
    resource is DataRecord
)
when {
    resource.retentionExpiry > context.now
    && resource.erasureRequested == false
    && (principal.role == "processor" || principal.role == "controller" || principal.role == "dpo")
};
