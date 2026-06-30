permit (
    principal is Worker,
    action == Action::"view",
    resource is Chart
)
when {
    principal.role == "nurse" ||
    principal.role == "doctor" ||
    principal.role == "administrator"
};

permit (
    principal is Worker,
    action == Action::"edit",
    resource is Chart
)
when {
    principal.role == "doctor" ||
    principal.role == "administrator"
};

permit (
    principal is Worker,
    action == Action::"archive",
    resource is Chart
)
when {
    principal.role == "administrator"
};