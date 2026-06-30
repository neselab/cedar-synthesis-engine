// Floor: a baseRole "manager" MUST be able to perform accessSensitive
// regardless of elevation/justification context (standing authority).
permit (
    principal is User,
    action == Action::"accessSensitive",
    resource is SensitiveResource
)
when {
    principal.baseRole == "manager"
};
