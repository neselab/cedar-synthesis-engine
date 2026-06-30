permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    (resource.owner == principal || principal in resource.editors) &&
    resource.isArchived == false &&
    (context.target.job != Job::"customer" ||
     (principal.job == Job::"distributor" && principal.customerId == context.target.customerId))
};