// Floor: a Responder of any clearance MUST be permitted to view a
// low-severity incident (severity <= 2). The lowest tier of the
// view decision tree requires only clearanceLevel >= 1, which every
// Responder satisfies (clearanceLevel range is 1-5).
permit (
    principal is Responder,
    action == Action::"view",
    resource is Incident
)
when {
    resource.severity <= 2
    && principal.clearanceLevel >= 1
};
