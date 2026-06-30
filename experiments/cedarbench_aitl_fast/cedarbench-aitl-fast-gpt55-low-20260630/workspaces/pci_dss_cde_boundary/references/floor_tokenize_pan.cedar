// Floor: a CDE-authorized System tokenizing a PAN record MUST be
// permitted. Per §8.8 the CDE check appears in the floor so it is
// jointly satisfiable with the ceiling.
permit (
    principal is System,
    action == Action::"tokenize",
    resource is PaymentRecord
)
when {
    principal.cdeAuthorized
    && resource.dataType == "PAN"
};
