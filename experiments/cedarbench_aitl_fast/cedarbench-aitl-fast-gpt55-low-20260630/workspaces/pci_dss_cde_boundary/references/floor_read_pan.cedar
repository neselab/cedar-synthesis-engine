// Floor: a CDE-authorized System reading a PAN record that is itself
// a CDE member MUST be permitted. Per §8.8, the CDE checks (both
// principal.cdeAuthorized and resource.cdeMember) appear in this floor
// so it is jointly satisfiable with the ceiling.
permit (
    principal is System,
    action == Action::"read",
    resource is PaymentRecord
)
when {
    resource.dataType == "PAN"
    && principal.cdeAuthorized
    && resource.cdeMember
};
