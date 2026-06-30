permit (
    principal is User,
    action == Action::"grantEditAccessToTemplate",
    resource is Template
) when {
    (principal == resource.owner ||
     (principal in resource.editors && principal.job == Job::"internal") ||
     (principal in resource.editorMarkets && principal.job == Job::"internal")) &&
    (!(context has targetUser) ||
     (context has targetUser && context.targetUser.job == Job::"internal")) &&
    (!(context has targetUser) ||
     (context has targetUser && context.targetUser.job != Job::"customer") ||
     (context has targetUser && principal.job == Job::"distributor" && principal.customerId == context.targetUser.customerId))
};