// Ceiling: view permitted only when the operator's baseRole is
// "user" or "admin". Guests are excluded. The certificate is not
// consulted for the view action.
permit (
    principal is Operator,
    action == Action::"view",
    resource is Resource
)
when {
    principal.baseRole == "user"
    || principal.baseRole == "admin"
};
