// Floor: a manager MUST be permitted to reassign any ticket.
permit (
    principal is Agent,
    action == Action::"reassign",
    resource is Ticket
)
when {
    principal.role == "manager"
};
