permit (
    principal is User,
    action == Action::"removeSelfAccessFromTemplate",
    resource is Template
) when {
    principal == resource.owner ||
    (principal in resource.viewers && principal.job == Job::"internal") ||
    (principal in resource.editors && principal.job == Job::"internal") ||
    (principal in resource.editorMarkets && principal.job == Job::"internal")
};