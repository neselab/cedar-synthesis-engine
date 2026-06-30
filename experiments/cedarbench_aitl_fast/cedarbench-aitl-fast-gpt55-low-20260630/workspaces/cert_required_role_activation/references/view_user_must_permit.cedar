// Floor: an operator with baseRole "user" MUST be able to view any
// resource. No certificate required.
permit (
    principal is Operator,
    action == Action::"view",
    resource is Resource
)
when {
    principal.baseRole == "user"
};
