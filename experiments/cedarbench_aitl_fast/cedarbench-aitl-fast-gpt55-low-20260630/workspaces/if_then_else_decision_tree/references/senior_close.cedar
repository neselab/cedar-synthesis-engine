// Floor: a Responder with clearanceLevel >= 5 MUST be permitted to
// close any incident. This is the only path to closeIncident.
permit (
    principal is Responder,
    action == Action::"closeIncident",
    resource is Incident
)
when {
    principal.clearanceLevel >= 5
};
