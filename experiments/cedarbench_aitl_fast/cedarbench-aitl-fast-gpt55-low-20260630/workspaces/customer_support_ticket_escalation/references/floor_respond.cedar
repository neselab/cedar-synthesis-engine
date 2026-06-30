// Floor: an agent with sufficient maxPriority MUST be permitted to respond.
permit (
    principal is Agent,
    action == Action::"respond",
    resource is Ticket
)
when {
    principal.maxPriority >= resource.priority
};
