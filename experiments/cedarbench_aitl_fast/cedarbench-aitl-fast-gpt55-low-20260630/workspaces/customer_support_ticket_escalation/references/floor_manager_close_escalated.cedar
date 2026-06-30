// Floor: a manager MUST be permitted to close an escalated ticket
// (subject to priority gate).
permit (
    principal is Agent,
    action == Action::"close",
    resource is Ticket
)
when {
    principal.role == "manager"
    && principal.maxPriority >= resource.priority
    && resource.isEscalated == true
};
