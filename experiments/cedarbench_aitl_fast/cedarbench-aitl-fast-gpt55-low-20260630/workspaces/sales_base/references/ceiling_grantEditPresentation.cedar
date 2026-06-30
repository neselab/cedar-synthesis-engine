permit (
    principal is User,
    action == Action::"grantEditAccessToPresentation",
    resource is Presentation
) when {
    (principal == resource.owner ||
     (principal in resource.editors && principal.job == Job::"internal")) &&
    context.target.job == Job::"internal" &&
    (context.target.job != Job::"customer" ||
     (principal.job == Job::"distributor" && principal.customerId == context.target.customerId))
};