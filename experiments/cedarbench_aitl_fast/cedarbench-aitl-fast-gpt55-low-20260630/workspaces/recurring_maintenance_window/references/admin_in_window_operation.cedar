// Floor: an admin MUST be able to perform `adminOperation` while the
// current time is inside the maintenance window.
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
