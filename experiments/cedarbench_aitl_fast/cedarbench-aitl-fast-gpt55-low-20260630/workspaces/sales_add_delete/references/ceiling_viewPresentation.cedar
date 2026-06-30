permit (
    principal is User,
    action == Action::"viewPresentation",
    resource is Presentation
) when {
    resource.owner == principal ||
    principal in resource.viewers ||
    principal in resource.editors
};