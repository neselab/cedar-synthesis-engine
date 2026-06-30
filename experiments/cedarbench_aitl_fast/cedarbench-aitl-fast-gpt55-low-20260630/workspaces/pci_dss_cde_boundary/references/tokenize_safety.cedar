// Ceiling for `tokenize`. Permitted only when:
//  - principal.cdeAuthorized AND
//  - resource.dataType == "PAN" (tokenizing a non-PAN is meaningless).
permit (
    principal is System,
    action == Action::"tokenize",
    resource is PaymentRecord
)
when {
    principal.cdeAuthorized
    && resource.dataType == "PAN"
};
