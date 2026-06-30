permit (
    principal is User,
    action == Action::"viewPresentation",
    resource is Presentation
) when {
    principal == resource.owner ||
    principal in resource.viewers ||
    (principal in resource.editors && principal.job == Job::"internal")
};