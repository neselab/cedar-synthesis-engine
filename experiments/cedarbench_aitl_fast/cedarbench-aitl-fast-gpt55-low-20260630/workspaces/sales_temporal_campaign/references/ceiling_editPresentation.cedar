permit (
    principal is User,
    action == Action::"editPresentation",
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
    )
};