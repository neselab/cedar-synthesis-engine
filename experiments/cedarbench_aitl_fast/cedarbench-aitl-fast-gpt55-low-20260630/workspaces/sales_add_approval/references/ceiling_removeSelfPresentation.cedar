permit (
    principal is User,
    action == Action::"removeSelfAccessFromPresentation",
    resource is Presentation
) when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.viewers
};