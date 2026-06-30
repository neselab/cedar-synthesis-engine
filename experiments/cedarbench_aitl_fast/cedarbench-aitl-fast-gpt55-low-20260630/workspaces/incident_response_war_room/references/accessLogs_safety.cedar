// Ceiling: accessLogs permitted only for leads and commanders.
// Applies to any incident regardless of active/resolved state.
permit (
    principal is Responder,
    action == Action::"accessLogs",
    resource is Incident
)
when {
    principal.role == "lead" || principal.role == "commander"
};
