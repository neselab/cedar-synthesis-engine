// Ceiling for `detokenize`. Highest restriction — permitted only when:
//  - principal.cdeAuthorized AND
//  - principal.auditCompliant AND
//  - resource.dataType == "TOKEN".
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
