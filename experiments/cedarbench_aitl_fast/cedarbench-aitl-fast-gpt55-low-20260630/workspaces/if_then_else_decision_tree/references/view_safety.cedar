// Ceiling: view permitted only when the responder's clearance meets
// the severity-tiered threshold. Written with nested if-then-else.
permit (
    principal is Responder,
    action == Action::"view",
    resource is Incident
)
when {
    if resource.severity >= 8 then principal.clearanceLevel >= 4
    else if resource.severity >= 5 then principal.clearanceLevel >= 3
    else if resource.severity >= 3 then principal.clearanceLevel >= 2
    else principal.clearanceLevel >= 1
};
