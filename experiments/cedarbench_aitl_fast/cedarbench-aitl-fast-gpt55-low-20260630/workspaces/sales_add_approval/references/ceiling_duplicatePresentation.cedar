permit (
    principal is User,
    action == Action::"duplicatePresentation",
    resource is Presentation
) when {
    resource.owner == principal ||
    principal in resource.editors ||
    (principal.job == Job::"internal" && principal in resource.viewers)
};