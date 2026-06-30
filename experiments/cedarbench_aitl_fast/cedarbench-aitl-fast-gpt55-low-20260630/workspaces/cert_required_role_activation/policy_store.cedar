// Policy store — verified policies appended here

// --- Verified (eval iteration 2) ---
permit (
    principal is Operator,
    action == Action::"view",
    resource is Resource
)
when {
    principal.baseRole == "user" || principal.baseRole == "admin"
};

permit (
    principal is Operator,
    action == Action::"executeAdmin",
    resource is Resource
)
when {
    principal.baseRole == "admin"
};

permit (
    principal is Operator,
    action == Action::"executeAdmin",
    resource is Resource
)
when {
    (context has cert && context.cert.validUntil > context.now) &&
    (context has cert && context.cert.claimedRole == "admin") &&
    (context has cert && context.cert.signer == "trusted-ca")
};
