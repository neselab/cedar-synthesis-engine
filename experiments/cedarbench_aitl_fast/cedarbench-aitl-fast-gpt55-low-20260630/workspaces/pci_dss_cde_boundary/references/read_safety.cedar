// Ceiling for `read`. Permitted only when ONE of:
//  - dataType is "PAN" and BOTH principal.cdeAuthorized AND resource.cdeMember,
//  - dataType is "TOKEN" (any system),
//  - dataType is "MASKED_PAN" (any system).
// Any candidate that permits read of PAN without the CDE checks, or
// that permits read of an unknown dataType, exceeds this ceiling.
permit (
    principal is System,
    action == Action::"read",
    resource is PaymentRecord
)
when {
    (resource.dataType == "PAN"
        && principal.cdeAuthorized
        && resource.cdeMember)
    || resource.dataType == "TOKEN"
    || resource.dataType == "MASKED_PAN"
};
