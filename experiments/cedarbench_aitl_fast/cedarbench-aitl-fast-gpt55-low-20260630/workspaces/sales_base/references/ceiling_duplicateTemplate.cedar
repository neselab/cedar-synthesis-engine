permit (
    principal is User,
    action == Action::"duplicateTemplate",
    resource is Template
) when {
    principal == resource.owner ||
    principal in resource.viewers ||
    (principal in resource.editors && principal.job == Job::"internal") ||
    principal in resource.viewerMarkets ||
    (principal in resource.editorMarkets && principal.job == Job::"internal")
};