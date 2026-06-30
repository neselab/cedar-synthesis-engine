permit (
    principal is Agent,
    action == Action::"respond",
    resource is Ticket
)
when {
    principal.maxPriority >= resource.priority
};

permit (
    principal is Agent,
    action == Action::"escalate",
    resource is Ticket
);

permit (
    principal is Agent,
    action == Action::"close",
    resource is Ticket
)
when {
    principal.maxPriority >= resource.priority &&
    (
        resource.isEscalated == false ||
        principal.role == "manager"
    )
};

permit (
    principal is Agent,
    action == Action::"reassign",
    resource is Ticket
)
when {
    principal.role == "manager"
};