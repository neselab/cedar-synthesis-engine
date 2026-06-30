permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" &&
    principal in resource.editors
};