// Ceiling: respond permitted only when BOTH the severity-tiered
// threshold AND the category-tiered threshold are satisfied.
permit (
    principal is Responder,
    action == Action::"respond",
    resource is Incident
)
when {
    (if resource.severity >= 8 then principal.clearanceLevel >= 4
     else if resource.severity >= 5 then principal.clearanceLevel >= 3
     else if resource.severity >= 3 then principal.clearanceLevel >= 2
     else principal.clearanceLevel >= 1)
    &&
    (if resource.category == "security" then principal.clearanceLevel >= 4
     else if resource.category == "data" then principal.clearanceLevel >= 3
     else principal.clearanceLevel >= 2)
};
