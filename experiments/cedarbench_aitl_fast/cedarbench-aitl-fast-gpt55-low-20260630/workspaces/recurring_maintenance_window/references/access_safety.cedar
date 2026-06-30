// Ceiling: `access` is permitted only when the user is oncall/admin
// (unconditional) OR the current time is NOT inside the maintenance
// window. "Inside the window" means
//   context.now >= context.windowStart
//   AND context.now < context.windowStart.offset(context.windowDuration)
permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "oncall"
    || principal.role == "admin"
    || (context.now < context.windowStart
        || context.now >= context.windowStart.offset(context.windowDuration))
};
