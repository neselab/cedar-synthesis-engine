permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
)
when {
    resource.owner == principal
};