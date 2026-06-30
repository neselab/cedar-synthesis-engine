permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "employee" &&
    context.currentHour >= 9 &&
    context.currentHour < 17
};

permit (
    principal is User,
    action == Action::"access",
    resource is System
)
when {
    principal.role == "manager" ||
    principal.role == "admin"
};

permit (
    principal is User,
    action == Action::"maintenance",
    resource is System
)
when {
    principal.role == "admin" &&
    (context.currentHour < 9 || context.currentHour >= 17)
};

forbid (
    principal is User,
    action == Action::"maintenance",
    resource is System
)
when {
    context.currentHour >= 9 &&
    context.currentHour < 17
};