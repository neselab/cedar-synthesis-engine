permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
)
when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorTeams
};