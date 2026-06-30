permit (
    principal is User,
    action == Action::"grantEditAccessToPresentation",
    resource is Presentation
)
when {
    (
        resource.owner == principal ||
        principal in resource.editors
    ) &&
    (
        principal.job == Job::"internal" ||
        (context.currentTime >= resource.campaignStart && context.currentTime <= resource.campaignEnd)
    ) &&
    context.target.job == Job::"internal"
};