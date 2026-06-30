permit (
    principal is User,
    action == Action::"removeSelfAccessFromPresentation",
    resource is Presentation
) when {
    principal == resource.owner ||
    principal in resource.viewers ||
    (principal in resource.editors && principal.job == Job::"internal")
};