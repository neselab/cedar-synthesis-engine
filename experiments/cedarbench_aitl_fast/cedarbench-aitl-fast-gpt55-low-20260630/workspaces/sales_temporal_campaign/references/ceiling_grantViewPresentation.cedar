permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
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
    (
        context.target.job != Job::"customer" ||
        (principal.job == Job::"distributor" && principal.customerId == context.target.customerId)
    )
};