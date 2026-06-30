permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    resource.owner == principal ||
    principal in resource.editors
};