// Ceiling: `adminOperation` is permitted only when the principal's role
// is "admin" AND the current time IS inside the maintenance window.
permit (
    principal is User,
    action == Action::"adminOperation",
    resource is System
)
when {
    principal.role == "admin"
    && context.now >= context.windowStart
    && context.now < context.windowStart.offset(context.windowDuration)
};
