// Floor: an officer with sufficient approvalLimit MUST be permitted to
// approve a low-risk submitted loan application.
permit (
    principal is Officer,
    action == Action::"approve",
    resource is LoanApplication
)
when {
    resource.isSubmitted
    && principal.approvalLimit >= resource.amount
    && resource.riskRating == "low"
};
