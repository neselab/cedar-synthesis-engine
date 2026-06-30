// Floor: an operator with baseRole "admin" MUST be able to view any
// resource.
permit (
    principal is Operator,
    action == Action::"view",
    resource is Resource
)
when {
    principal.baseRole == "admin"
};
