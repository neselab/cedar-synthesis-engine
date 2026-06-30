// Floor: a team member MUST be able to edit a non-confidential document
// owned by their team.
permit (
    principal is Employee,
    action == Action::"edit",
    resource is Document
)
when {
    principal in resource.ownerTeam
    && resource.classification != "confidential"
};
