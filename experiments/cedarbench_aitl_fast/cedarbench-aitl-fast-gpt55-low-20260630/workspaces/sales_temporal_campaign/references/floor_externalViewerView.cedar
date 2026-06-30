permit (
    principal is User,
    action == Action::"viewPresentation",
    resource is Presentation
)
when {
    principal in resource.viewers &&
    context.currentTime >= resource.campaignStart &&
    context.currentTime <= resource.campaignEnd
};