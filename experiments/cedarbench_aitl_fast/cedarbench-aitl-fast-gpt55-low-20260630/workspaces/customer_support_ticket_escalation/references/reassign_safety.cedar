// Ceiling: reassign is permitted ONLY when the agent is a manager.
permit (
    principal is Agent,
    action == Action::"reassign",
    resource is Ticket
)
when {
    principal.role == "manager"
};
