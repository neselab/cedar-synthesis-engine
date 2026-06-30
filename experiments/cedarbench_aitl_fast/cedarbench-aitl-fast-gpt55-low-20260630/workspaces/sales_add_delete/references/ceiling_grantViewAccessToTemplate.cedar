permit (
    principal is User,
    action == Action::"grantViewAccessToTemplate",
    resource is Template
) when {
    (resource.owner == principal || principal in resource.editors || principal in resource.editorMarkets) &&
    (!(context has targetUser) ||
     (context has targetUser &&
      (context.targetUser.job != Job::"customer" ||
       (principal.job == Job::"distributor" && principal.customerId == context.targetUser.customerId))))
};