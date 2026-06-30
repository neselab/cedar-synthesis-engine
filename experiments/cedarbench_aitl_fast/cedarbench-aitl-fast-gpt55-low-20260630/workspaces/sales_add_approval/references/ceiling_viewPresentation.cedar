permit (
    principal is User,
    action == Action::"viewPresentation",
    resource is Presentation
) when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.viewers
};