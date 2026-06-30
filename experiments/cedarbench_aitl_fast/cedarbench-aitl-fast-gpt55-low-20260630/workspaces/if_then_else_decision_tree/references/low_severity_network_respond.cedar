// Floor: a Responder with clearanceLevel >= 2 MUST be permitted to
// respond to a low-severity (severity <= 2) "network" incident.
// Severity branch: lowest tier requires clearance >= 1 (satisfied).
// Category branch: "network" falls into the else, requiring >= 2.
permit (
    principal is Responder,
    action == Action::"respond",
    resource is Incident
)
when {
    resource.severity <= 2
    && resource.category == "network"
    && principal.clearanceLevel >= 2
};
