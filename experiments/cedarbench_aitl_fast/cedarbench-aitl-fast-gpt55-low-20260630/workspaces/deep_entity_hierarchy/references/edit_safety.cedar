// Ceiling: edit permitted only when same team AND NOT confidential.
permit (
    principal is Employee,
    action == Action::"edit",
    resource is Document
)
when {
    principal in resource.ownerTeam
    && resource.classification != "confidential"
};
