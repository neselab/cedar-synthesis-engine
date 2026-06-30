// Ceiling: closeIncident permitted only when the responder has
// clearanceLevel >= 5. No severity- or category-conditional relief.
permit (
    principal is Responder,
    action == Action::"closeIncident",
    resource is Incident
)
when {
    principal.clearanceLevel >= 5
};
