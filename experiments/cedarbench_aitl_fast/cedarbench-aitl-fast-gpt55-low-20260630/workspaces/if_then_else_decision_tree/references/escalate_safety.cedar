// Ceiling: escalate permitted unconditionally when severity < 8;
// requires clearanceLevel >= 4 when severity >= 8.
permit (
    principal is Responder,
    action == Action::"escalate",
    resource is Incident
)
when {
    if resource.severity >= 8 then principal.clearanceLevel >= 4
    else true
};
