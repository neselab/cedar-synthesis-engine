permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
)
when {
    principal in resource.editorTeams
};