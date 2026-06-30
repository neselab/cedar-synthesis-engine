// Floor: a baseRole "user" MUST be able to perform accessNormal.
// (Within the ceiling: any of the three valid roles is permitted.)
permit (
    principal is User,
    action == Action::"accessNormal",
    resource is SensitiveResource
)
when {
    principal.baseRole == "user"
};
