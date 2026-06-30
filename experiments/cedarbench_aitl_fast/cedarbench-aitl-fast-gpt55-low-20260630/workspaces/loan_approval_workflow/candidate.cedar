permit (
    principal is Officer,
    action == Action::"submit",
    resource is LoanApplication
)
when {
    principal.role == "analyst" &&
    !resource.isSubmitted
};

permit (
    principal is Officer,
    action == Action::"review",
    resource is LoanApplication
)
when {
    resource.isSubmitted
};

permit (
    principal is Officer,
    action == Action::"approve",
    resource is LoanApplication
)
when {
    resource.isSubmitted &&
    principal.approvalLimit >= resource.amount &&
    (
        resource.riskRating != "high" ||
        principal.role == "director" ||
        principal.role == "vp"
    )
};

permit (
    principal is Officer,
    action == Action::"reject",
    resource is LoanApplication
)
when {
    resource.isSubmitted
};

permit (
    principal is Officer,
    action == Action::"escalate",
    resource is LoanApplication
)
when {
    resource.isSubmitted
};