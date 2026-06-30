// Floor: a senior Responder (clearanceLevel >= 4) MUST be permitted
// to view a high-severity incident (severity >= 8). This is the
// top branch of the view decision tree.
permit (
    principal is Responder,
    action == Action::"view",
    resource is Incident
)
when {
    resource.severity >= 8
    && principal.clearanceLevel >= 4
};
