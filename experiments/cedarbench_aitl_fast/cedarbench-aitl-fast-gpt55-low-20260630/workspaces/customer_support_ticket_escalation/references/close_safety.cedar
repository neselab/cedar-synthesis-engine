// Ceiling: close is permitted ONLY when agent's maxPriority >= ticket priority
// AND either the ticket is not escalated OR the agent is a manager.
permit (
    principal is Agent,
    action == Action::"close",
    resource is Ticket
)
when {
    principal.maxPriority >= resource.priority
    && (resource.isEscalated == false || principal.role == "manager")
};
