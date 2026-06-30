// Ceiling: respond is permitted ONLY when agent's maxPriority >= ticket priority.
permit (
    principal is Agent,
    action == Action::"respond",
    resource is Ticket
)
when {
    principal.maxPriority >= resource.priority
};
