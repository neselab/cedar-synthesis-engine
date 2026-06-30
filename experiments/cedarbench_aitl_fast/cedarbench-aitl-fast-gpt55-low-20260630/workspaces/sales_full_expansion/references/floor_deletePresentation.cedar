permit (
    principal is User,
    action == Action::"deletePresentation",
    resource is Presentation
) when {
    resource.owner == principal
};