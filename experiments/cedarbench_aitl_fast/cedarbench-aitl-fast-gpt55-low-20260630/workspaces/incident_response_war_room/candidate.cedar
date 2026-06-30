permit (
  principal is Responder,
  action == Action::"viewDetails",
  resource is Incident
)
when {
  resource.isActive == true
};

permit (
  principal is Responder,
  action == Action::"updateStatus",
  resource is Incident
)
when {
  resource.isActive == true &&
  (
    (resource.severity == "sev1" && principal.clearanceLevel >= 3) ||
    (resource.severity == "sev2" && principal.clearanceLevel >= 2) ||
    (resource.severity == "sev3" && principal.clearanceLevel >= 1)
  )
};

permit (
  principal is Responder,
  action == Action::"accessLogs",
  resource is Incident
)
when {
  principal.role == "lead" ||
  principal.role == "commander"
};

permit (
  principal is Responder,
  action == Action::"declareResolved",
  resource is Incident
)
when {
  principal.role == "commander" &&
  resource.isActive == true
};