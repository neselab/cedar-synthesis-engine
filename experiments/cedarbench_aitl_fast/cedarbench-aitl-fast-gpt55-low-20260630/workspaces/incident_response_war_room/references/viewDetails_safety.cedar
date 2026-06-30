// Ceiling: viewDetails permitted only on active incidents.
permit (
    principal is Responder,
    action == Action::"viewDetails",
    resource is Incident
)
when {
    resource.isActive == true
};
