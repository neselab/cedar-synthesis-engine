forbid (
    principal is User,
    action in [Action::"initiate", Action::"approve", Action::"release", Action::"reject"],
    resource is PayrollEntry
)
when {
    resource.status == "released" || resource.status == "rejected"
};

forbid (
    principal is User,
    action == Action::"approve",
    resource is PayrollEntry
)
when {
    resource.amount >= 50000 &&
    principal.role != "cfo"
};

permit (
    principal is User,
    action == Action::"initiate",
    resource is PayrollEntry
)
when {
    principal.role == "clerk" &&
    resource.status == "draft"
};

permit (
    principal is User,
    action == Action::"approve",
    resource is PayrollEntry
)
when {
    (principal.role == "manager" || principal.role == "cfo") &&
    resource.status == "pending_approval" &&
    principal != resource.initiator
};

permit (
    principal is User,
    action == Action::"release",
    resource is PayrollEntry
)
when {
    principal.role == "cfo" &&
    resource.status == "approved"
};

permit (
    principal is User,
    action == Action::"reject",
    resource is PayrollEntry
)
when {
    (principal.role == "manager" || principal.role == "cfo") &&
    resource.status == "pending_approval"
};

permit (
    principal is User,
    action == Action::"read",
    resource is PayrollEntry
);