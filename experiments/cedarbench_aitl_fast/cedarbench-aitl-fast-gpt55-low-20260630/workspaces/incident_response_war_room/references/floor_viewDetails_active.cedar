// Floor: any responder MUST be permitted to view an active incident.
// No global forbids, so no exclusions needed (SS8.8).
permit (
    principal is Responder,
    action == Action::"viewDetails",
    resource is Incident
)
when {
    resource.isActive == true
};
