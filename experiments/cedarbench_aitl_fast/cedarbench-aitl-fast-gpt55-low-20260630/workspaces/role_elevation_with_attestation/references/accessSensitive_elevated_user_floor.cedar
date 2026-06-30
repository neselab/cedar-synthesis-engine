// Floor: a baseRole "user" with elevationGranted=true AND a non-empty
// elevationJustification in context MUST be permitted to accessSensitive.
permit (
    principal is User,
    action == Action::"accessSensitive",
    resource is SensitiveResource
)
when {
    principal.baseRole == "user"
    && principal.elevationGranted == true
    && context has elevationJustification
    && context.elevationJustification != ""
};
