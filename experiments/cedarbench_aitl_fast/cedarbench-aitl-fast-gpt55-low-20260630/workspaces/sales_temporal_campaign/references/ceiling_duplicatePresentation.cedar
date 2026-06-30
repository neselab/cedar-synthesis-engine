permit (
    principal is User,
    action == Action::"duplicatePresentation",
    resource is Presentation
)
when {
    (
        (principal.job == Job::"internal" && principal in resource.viewers) ||
        resource.owner == principal ||
        principal in resource.editors
    ) &&
    (
        principal.job == Job::"internal" ||
        (context.currentTime >= resource.campaignStart && context.currentTime <= resource.campaignEnd)
    )
};