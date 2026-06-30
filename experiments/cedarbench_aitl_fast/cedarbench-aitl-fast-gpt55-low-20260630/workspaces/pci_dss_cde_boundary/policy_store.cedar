// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is System,
    action == Action::"read",
    resource is PaymentRecord
)
when {
    resource.dataType == "PAN" &&
    principal.cdeAuthorized &&
    resource.cdeMember
};

permit (
    principal is System,
    action == Action::"read",
    resource is PaymentRecord
)
when {
    resource.dataType == "TOKEN"
};

permit (
    principal is System,
    action == Action::"read",
    resource is PaymentRecord
)
when {
    resource.dataType == "MASKED_PAN"
};

permit (
    principal is System,
    action == Action::"tokenize",
    resource is PaymentRecord
)
when {
    principal.cdeAuthorized &&
    resource.dataType == "PAN"
};

permit (
    principal is System,
    action == Action::"detokenize",
    resource is PaymentRecord
)
when {
    principal.cdeAuthorized &&
    principal.auditCompliant &&
    resource.dataType == "TOKEN"
};

permit (
    principal is System,
    action == Action::"audit",
    resource is PaymentRecord
)
when {
    resource.dataType != "PAN"
};

permit (
    principal is System,
    action == Action::"audit",
    resource is PaymentRecord
)
when {
    resource.dataType == "PAN" &&
    principal.cdeAuthorized
};
