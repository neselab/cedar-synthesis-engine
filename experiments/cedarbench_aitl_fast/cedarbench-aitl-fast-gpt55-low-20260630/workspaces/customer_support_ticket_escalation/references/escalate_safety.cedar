// Ceiling: escalate is permitted unconditionally for any agent on any ticket.
permit (
    principal is Agent,
    action == Action::"escalate",
    resource is Ticket
);
