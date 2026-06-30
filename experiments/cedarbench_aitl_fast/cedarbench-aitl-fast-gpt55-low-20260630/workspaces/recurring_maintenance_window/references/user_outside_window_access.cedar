// Floor: an ordinary user MUST be able to access the system when the
// current time is outside the maintenance window.
permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "user"
    && (context.now < context.windowStart
        || context.now >= context.windowStart.offset(context.windowDuration))
};
