// Ceiling: updateStatus permitted only on active incidents when the
// responder's clearance level meets the severity threshold.
//   sev1 -> clearanceLevel >= 3
//   sev2 -> clearanceLevel >= 2
//   sev3 -> clearanceLevel >= 1
permit (
    principal is Responder,
    action == Action::"updateStatus",
    resource is Incident
)
when {
    resource.isActive == true
    && (
        (resource.severity == "sev1" && principal.clearanceLevel >= 3)
        || (resource.severity == "sev2" && principal.clearanceLevel >= 2)
        || (resource.severity == "sev3" && principal.clearanceLevel >= 1)
    )
};
