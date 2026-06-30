// Floor: a responder with clearanceLevel >= 2 MUST be permitted to
// updateStatus on an active sev2 incident.
// No global forbids, so no exclusions needed (SS8.8).
permit (
    principal is Responder,
    action == Action::"updateStatus",
    resource is Incident
)
when {
    resource.isActive == true
    && resource.severity == "sev2"
    && principal.clearanceLevel >= 2
};
