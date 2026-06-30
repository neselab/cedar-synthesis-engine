permit (
    principal is User,
    action == Action::"viewPresentation",
    resource is Presentation
) when {
    principal.job != Job::"internal" &&
    principal in resource.viewers
};