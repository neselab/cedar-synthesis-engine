permit (
    principal is User,
    action == Action::"View",
    resource is Document
) when {
    context.requestTime >= resource.embargoUntil ||
    principal in Role::"PrincipalInvestigator"
};