// Floor: any agent MUST be permitted to escalate any ticket.
permit (
    principal is Agent,
    action == Action::"escalate",
    resource is Ticket
);
