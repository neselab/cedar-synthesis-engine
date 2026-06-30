permit (
    principal is User,
    action == Action::"grantEditAccessToPresentation",
    resource is Presentation
) when {
    (resource.owner == principal || principal in resource.editors) &&
    context.target.job == Job::"internal"
};