// Floor: a team member MUST be able to delete a public document
// owned by their team.
permit (
    principal is Employee,
    action == Action::"delete",
    resource is Document
)
when {
    principal in resource.ownerTeam
    && resource.classification == "public"
};
