// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "user" &&
    (
        context.now < context.windowStart ||
        context.now >= context.windowStart.offset(context.windowDuration)
    )
};

permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "oncall"
};

permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "admin"
};

permit (
    principal is User,
    action == Action::"adminOperation",
    resource is System
)
when {
    principal.role == "admin" &&
    context.now >= context.windowStart &&
    context.now < context.windowStart.offset(context.windowDuration)
};

forbid (
    principal is User,
    action == Action::"adminOperation",
    resource is System
)
when {
    context.now < context.windowStart ||
    context.now >= context.windowStart.offset(context.windowDuration)
};
