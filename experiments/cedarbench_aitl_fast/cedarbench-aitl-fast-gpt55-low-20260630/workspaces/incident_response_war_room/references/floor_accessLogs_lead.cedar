// Floor: a lead MUST be permitted to access logs on any incident
// (regardless of active/resolved state).
// No global forbids, so no exclusions needed (SS8.8).
permit (
    principal is Responder,
    action == Action::"accessLogs",
    resource is Incident
)
when {
    principal.role == "lead"
};
