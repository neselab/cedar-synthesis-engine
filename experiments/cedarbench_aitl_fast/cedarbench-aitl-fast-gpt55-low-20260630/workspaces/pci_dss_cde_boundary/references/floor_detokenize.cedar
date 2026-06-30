// Floor: a System that is BOTH cdeAuthorized AND auditCompliant
// detokenizing a TOKEN MUST be permitted. Per §8.8 both gates appear
// in the floor so it is jointly satisfiable with the ceiling.
permit (
    principal is System,
    action == Action::"detokenize",
    resource is PaymentRecord
)
when {
    principal.cdeAuthorized
    && principal.auditCompliant
    && resource.dataType == "TOKEN"
};
