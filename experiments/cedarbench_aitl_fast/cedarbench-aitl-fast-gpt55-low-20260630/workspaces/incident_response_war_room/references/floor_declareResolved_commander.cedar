// Floor: a commander MUST be permitted to declare an active incident resolved.
// No global forbids, so no exclusions needed (SS8.8).
permit (
    principal is Responder,
    action == Action::"declareResolved",
    resource is Incident
)
when {
    principal.role == "commander" && resource.isActive == true
};
