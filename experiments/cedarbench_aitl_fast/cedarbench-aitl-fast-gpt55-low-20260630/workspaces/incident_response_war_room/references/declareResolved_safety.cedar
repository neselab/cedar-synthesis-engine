// Ceiling: declareResolved permitted only for commanders on active incidents.
permit (
    principal is Responder,
    action == Action::"declareResolved",
    resource is Incident
)
when {
    principal.role == "commander" && resource.isActive == true
};
