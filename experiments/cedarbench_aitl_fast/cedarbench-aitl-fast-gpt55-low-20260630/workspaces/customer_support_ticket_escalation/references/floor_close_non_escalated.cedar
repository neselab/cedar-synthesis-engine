// Floor: an agent with sufficient maxPriority MUST be permitted to close
// a non-escalated ticket.
// §8.8: includes resource.isEscalated == false to remain satisfiable
// alongside the close_safety ceiling (which requires !escalated for
// non-managers).
permit (
    principal is Agent,
    action == Action::"close",
    resource is Ticket
)
when {
    principal.maxPriority >= resource.priority
    && resource.isEscalated == false
};
