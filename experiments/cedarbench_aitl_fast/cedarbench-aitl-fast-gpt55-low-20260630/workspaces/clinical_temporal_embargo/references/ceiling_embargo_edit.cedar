permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
) when {
    context.requestTime >= resource.embargoUntil ||
    principal in Role::"PrincipalInvestigator"
};