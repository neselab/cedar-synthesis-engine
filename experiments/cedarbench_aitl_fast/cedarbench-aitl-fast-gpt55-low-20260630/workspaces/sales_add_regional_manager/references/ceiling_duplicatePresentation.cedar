permit (
    principal is User,
    action == Action::"duplicatePresentation",
    resource is Presentation
) when {
    (principal.job == Job::"internal" && principal in resource.viewers) ||
    resource.owner == principal ||
    principal in resource.editors
};