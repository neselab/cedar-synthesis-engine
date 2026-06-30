permit (
    principal is User,
    action == Action::"duplicatePresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" &&
    (principal == resource.owner ||
     principal in resource.viewers ||
     principal in resource.editors)
};