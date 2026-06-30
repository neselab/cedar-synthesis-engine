// Floor: a team member MUST be able to view a confidential document
// owned by their team.
permit (
    principal is Employee,
    action == Action::"view",
    resource is Document
)
when {
    resource.classification == "confidential"
    && principal in resource.ownerTeam
};
