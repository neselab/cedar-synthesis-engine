// Ceiling: modify is permitted only when the resource's tenant is in
// the principal's adminOf set. Same scoping as view — admin authority
// in the resource's tenant is required.
permit (
    principal is User,
    action == Action::"modify",
    resource is Resource
)
when {
    principal.adminOf.contains(resource.tenant)
};
