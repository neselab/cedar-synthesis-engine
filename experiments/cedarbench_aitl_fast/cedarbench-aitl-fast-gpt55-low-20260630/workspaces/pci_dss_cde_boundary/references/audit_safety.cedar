// Ceiling for `audit`. Permitted only when:
//  - resource.dataType is NOT "PAN" (any system can audit non-PAN), OR
//  - principal.cdeAuthorized (auditing PAN requires CDE authorization).
permit (
    principal is System,
    action == Action::"audit",
    resource is PaymentRecord
)
when {
    resource.dataType != "PAN"
    || principal.cdeAuthorized
};
