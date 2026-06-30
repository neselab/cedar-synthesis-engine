permit (
    principal,
    action == Action::"viewAccount",
    resource
)
when {
    principal is BankCustomer &&
    resource is BankCustomer &&
    (
        principal.kycTier == "SDD" ||
        principal.kycTier == "CDD" ||
        principal.kycTier == "EDD"
    )
};

permit (
    principal,
    action == Action::"transferOut",
    resource
)
when {
    principal is BankCustomer &&
    resource is Transaction &&
    resource.amount < 10000 &&
    (
        principal.kycTier == "SDD" ||
        principal.kycTier == "CDD" ||
        principal.kycTier == "EDD"
    )
};

permit (
    principal,
    action == Action::"transferOut",
    resource
)
when {
    principal is BankCustomer &&
    resource is Transaction &&
    resource.amount >= 10000 &&
    resource.amount <= 100000 &&
    (
        principal.kycTier == "CDD" ||
        principal.kycTier == "EDD"
    )
};

permit (
    principal,
    action == Action::"transferOut",
    resource
)
when {
    principal is BankCustomer &&
    resource is Transaction &&
    resource.amount > 100000 &&
    principal.kycTier == "EDD" &&
    principal.uboVerified == true &&
    principal.adverseMediaClean == true
};

permit (
    principal,
    action == Action::"openProduct",
    resource
)
when {
    principal is BankCustomer &&
    resource is BankCustomer &&
    principal.riskScore > 70 &&
    principal.kycTier == "EDD" &&
    principal.uboVerified == true &&
    principal.adverseMediaClean == true
};

permit (
    principal,
    action == Action::"openProduct",
    resource
)
when {
    principal is BankCustomer &&
    resource is BankCustomer &&
    principal.riskScore <= 70 &&
    (
        principal.kycTier == "CDD" ||
        principal.kycTier == "EDD"
    )
};

permit (
    principal,
    action == Action::"escalateReview",
    resource
)
when {
    principal is BankCustomer &&
    resource is BankCustomer &&
    (
        principal.kycTier == "CDD" ||
        principal.kycTier == "EDD"
    )
};