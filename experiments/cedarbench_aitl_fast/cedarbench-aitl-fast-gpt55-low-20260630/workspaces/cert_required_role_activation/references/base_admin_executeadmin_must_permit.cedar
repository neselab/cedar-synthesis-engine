// Floor: an operator with baseRole "admin" MUST be able to perform
// executeAdmin on any resource without presenting a certificate.
permit (
    principal is Operator,
    action == Action::"executeAdmin",
    resource is Resource
)
when {
    principal.baseRole == "admin"
};
